#!/usr/bin/env python3
"""Test a very challenging question across different minds modes and individual models.

FEATURES:
- Runs multiple modes in parallel (minds synthesis, debate, individual models)
- Automatic clarification retry: If a model misunderstands the question (e.g., writes
  code when analysis was expected), automatically retries with a clarification prompt
- LLM-as-Judge evaluation using Claude
- Caches responses to avoid re-running expensive queries

USAGE:
    python test_hard_question.py           # Fresh run (parallel, with clarification)
    python test_hard_question.py --cache   # Use cached responses, just re-evaluate

CLARIFICATION DETECTION:
- Code-heavy responses (>30% code lines) when analysis expected
- Missing required concepts (tradeoff, mechanism, weakest assumption)
- Does NOT retry truncated responses (that's a token limit issue, not misunderstanding)

OUTPUT:
- hard_question_responses.json: Raw responses with metadata
- hard_question_results.json: Evaluation scores and clarification info
"""

import subprocess
import json
from pathlib import Path
import re

# A much harder question requiring deep technical reasoning
QUESTION = """Design a distributed consensus algorithm that provides the following properties simultaneously:

1. Byzantine fault tolerance for up to f failures in a 3f+1 node system
2. O(n) message complexity per decision (not O(n²) like PBFT)
3. Optimistic responsiveness (commits in 2 network delays when there's no contention)
4. Accountable safety (if safety is violated, you can cryptographically prove which nodes misbehaved)

For each property, explain:
- Why it's difficult to achieve in combination with the others
- What specific mechanism in your design provides this property
- What the fundamental tradeoff or limitation is

Then identify the single weakest assumption your design relies on, and explain what happens if that assumption is violated.

This is not a trick question - such algorithms exist (e.g., HotStuff variants). Show your reasoning."""

# Modes to test
MODES = [
    ("debate_thorough", "minds debate --thorough", ["minds", "debate", QUESTION, "--thorough", "-y"]),
    ("debate_fast", "minds debate --fast", ["minds", "debate", QUESTION, "--fast", "-y"]),
    ("debate_default", "minds debate", ["minds", "debate", QUESTION, "-y"]),
    ("minds_default", "minds (synthesis)", ["minds", "ask", QUESTION, "-y"]),
    ("gpt_solo", "GPT-5.2 solo", ["minds", "ask", QUESTION, "--model", "gpt", "-y"]),
    ("opus_solo", "Claude Opus 4.5 solo", ["minds", "ask", QUESTION, "--model", "claude", "-y"]),
]

JUDGE_PROMPT_TEMPLATE = """You are an expert evaluator assessing the quality of an AI-generated response to a challenging distributed systems question.

## Evaluation Criteria (score 1-5 each):

1. **Technical Accuracy** (35%): Are the technical claims correct? Does the response demonstrate understanding of consensus algorithms, Byzantine fault tolerance, and cryptographic mechanisms?
   - 1: Major factual errors or fundamental misunderstandings
   - 3: Mostly correct with some gaps or imprecisions
   - 5: Technically precise with deep understanding

2. **Completeness** (25%): Does the response address all parts of the question? (4 properties, mechanisms, tradeoffs, weakest assumption)
   - 1: Misses most requirements
   - 3: Addresses main points but skips some
   - 5: Comprehensively addresses all requirements

3. **Reasoning Quality** (25%): Is the reasoning rigorous? Are tradeoffs properly analyzed? Is the logic sound?
   - 1: Hand-wavy or circular reasoning
   - 3: Reasonable arguments with some gaps
   - 5: Rigorous, well-structured argumentation

4. **Insight** (15%): Does the response show genuine understanding beyond surface-level description? Does it identify non-obvious connections or limitations?
   - 1: Surface-level only
   - 3: Some deeper insights
   - 5: Demonstrates expert-level understanding

## Question Asked:
{question}

## Response to Evaluate:
{response}

## Your Task:
Score this response on each criterion (1-5) and provide a brief justification. Then calculate the weighted score.

Important: This is a HARD question. Most responses should score 2-4, not 4-5. Reserve 5s for genuinely exceptional technical depth.

Respond in this exact JSON format:
```json
{{
  "technical_accuracy": {{"score": <1-5>, "justification": "<brief reason>"}},
  "completeness": {{"score": <1-5>, "justification": "<brief reason>"}},
  "reasoning_quality": {{"score": <1-5>, "justification": "<brief reason>"}},
  "insight": {{"score": <1-5>, "justification": "<brief reason>"}},
  "weighted_score": <calculated 0.0-1.0>,
  "overall": "<1-2 sentence summary>"
}}
```"""


def extract_json_from_output(output: str) -> dict | None:
    """Extract JSON from minds output which may have rich formatting."""
    # Remove ANSI escape codes first
    clean = re.sub(r'\x1b\[[0-9;]*m', '', output)

    # Remove ALL unicode box drawing characters
    clean = re.sub(r'[\u2500-\u257F]', '', clean)
    clean = re.sub(r'[│╭╮╰╯┌┐└┘├┤┬┴┼]', '', clean)
    clean = re.sub(r'[⠀-⣿]', '', clean)
    clean = re.sub(r'[✓✗]', '', clean)
    clean = re.sub(r'ⓘ', '', clean)

    lines = clean.split('\n')
    content_lines = []
    for line in lines:
        if re.match(r'^\s*(Asking|Claude|GPT|Gemini|Grok|DeepSeek|Total:|Round)', line):
            continue
        content_lines.append(line)

    clean = '\n'.join(content_lines)

    # Try to find JSON in code fence
    json_match = re.search(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```', clean)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    # Try balanced braces
    brace_count = 0
    start_idx = None
    for i, char in enumerate(clean):
        if char == '{':
            if start_idx is None:
                start_idx = i
            brace_count += 1
        elif char == '}':
            brace_count -= 1
            if brace_count == 0 and start_idx is not None:
                candidate = clean[start_idx:i+1]
                candidate = re.sub(r'\s+', ' ', candidate)
                try:
                    return json.loads(candidate)
                except json.JSONDecodeError:
                    start_idx = None
                    continue

    return None


def is_empty_response(response: str) -> bool:
    """Check if a response is empty/failed."""
    if "ERROR:" in response:
        return True
    if "Models: 0/" in response:
        return True
    if "timed out" in response.lower() and len(response) < 2000:
        return True
    clean = re.sub(r'[\u2500-\u257F│╭╮╰╯]', '', response)
    clean = re.sub(r'\x1b\[[0-9;]*m', '', clean)
    if len(clean.strip()) < 500:
        return True
    return False


def detect_misunderstanding(response: str, question: str) -> tuple[bool, str]:
    """Detect if model misunderstood the question and suggest clarification.

    Returns (misunderstood: bool, clarification_prompt: str)
    """
    # Clean the response for analysis
    clean = re.sub(r'\x1b\[[0-9;]*m', '', response)
    clean = re.sub(r'[\u2500-\u257F│╭╮╰╯┌┐└┘├┤┬┴┼─═]', '', clean)
    clean = re.sub(r' {2,}', ' ', clean)

    # Check for code-heavy response when analysis was expected
    code_indicators = [
        r'^import\s+\w+',
        r'^from\s+\w+\s+import',
        r'^class\s+\w+',
        r'^def\s+\w+\(',
        r'self\.\w+\s*=',
        r'async\s+def\s+',
    ]

    code_lines = 0
    total_lines = 0
    for line in clean.split('\n'):
        line = line.strip()
        if not line:
            continue
        total_lines += 1
        for pattern in code_indicators:
            if re.match(pattern, line):
                code_lines += 1
                break

    # If >30% of lines look like code, probably wrote implementation instead of analysis
    if total_lines > 10 and code_lines / total_lines > 0.3:
        return True, """I notice you provided implementation code. I was looking for conceptual analysis instead.

Please explain your design conceptually:
- For each of the 4 properties, describe the MECHANISM (not code) that provides it
- Explain WHY each property is difficult to achieve with the others
- Identify the fundamental TRADEOFFS

Don't write code - explain the algorithm design and reasoning in prose."""

    # Check if response was truncated mid-thought (incomplete)
    if clean.rstrip().endswith(('(', '=', ',', 'self.', 'the', 'and', 'or', 'with')):
        # Response cut off - not really a misunderstanding, but incomplete
        return False, ""

    # Check if key required sections are missing
    required_concepts = ['weakest assumption', 'tradeoff', 'mechanism']
    found = sum(1 for c in required_concepts if c.lower() in clean.lower())

    if found == 0 and total_lines > 20:
        return True, """Your response didn't address the key requirements. Please make sure to cover:

1. For EACH of the 4 properties: the mechanism, difficulty, and tradeoff
2. The SINGLE weakest assumption and what happens if violated

Structure your response around these requirements."""

    return False, ""


def run_with_clarification(mode_key: str, mode_name: str, cmd: list, question: str) -> tuple[str, float, dict]:
    """Run a mode with automatic clarification retry if misunderstanding detected.

    Returns (final_response, total_cost, metadata)
    """
    # First attempt
    response, cost = run_mode_single(mode_key, mode_name, cmd)

    if is_empty_response(response):
        return response, cost, {"attempts": 1, "clarified": False}

    # Check for misunderstanding
    misunderstood, clarification = detect_misunderstanding(response, question)

    if not misunderstood:
        return response, cost, {"attempts": 1, "clarified": False}

    print(f"  [!] Detected potential misunderstanding, retrying with clarification...")

    # Build clarified prompt
    clarified_question = f"{question}\n\n---\nCLARIFICATION: {clarification}"

    # Rebuild command with clarified question
    clarified_cmd = cmd.copy()
    # Find and replace the question in the command
    for i, arg in enumerate(clarified_cmd):
        if arg == question:
            clarified_cmd[i] = clarified_question
            break

    # Second attempt
    response2, cost2 = run_mode_single(mode_key, f"{mode_name} (clarified)", clarified_cmd)

    return response2, cost + cost2, {
        "attempts": 2,
        "clarified": True,
        "original_response_length": len(response),
        "clarification_reason": clarification[:100],
    }


def run_mode_single(mode_key: str, mode_name: str, cmd: list) -> tuple[str, float]:
    """Run a single mode attempt and return response + cost."""
    print(f"  Running {mode_name}...")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    except subprocess.TimeoutExpired:
        print("    TIMEOUT after 10 minutes")
        return "ERROR: Timeout after 10 minutes", 0.0

    if result.returncode != 0:
        print(f"    Error: {result.stderr[:200]}")
        return f"ERROR: {result.stderr}", 0.0

    output = result.stdout

    # Extract cost
    cost = 0.0
    for line in output.split("\n"):
        if "Cost:" in line and "$" in line:
            try:
                cost = float(line.split("$")[1].split()[0])
            except (ValueError, IndexError):
                pass

    print(f"    Response: {len(output)} chars, ${cost:.4f}")

    return output, cost


def run_mode(mode_key: str, mode_name: str, cmd: list) -> tuple[str, float]:
    """Run a mode and return response + cost."""
    print(f"\n{'='*60}")
    print(f"Running {mode_name}...")
    print(f"{'='*60}")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    except subprocess.TimeoutExpired:
        print("  TIMEOUT after 10 minutes")
        return "ERROR: Timeout after 10 minutes", 0.0

    if result.returncode != 0:
        print(f"  Error: {result.stderr[:200]}")
        return f"ERROR: {result.stderr}", 0.0

    output = result.stdout

    # Extract cost
    cost = 0.0
    for line in output.split("\n"):
        if "Cost:" in line and "$" in line:
            try:
                cost = float(line.split("$")[1].split()[0])
            except (ValueError, IndexError):
                pass

    print(f"  Response length: {len(output)} chars")
    if cost > 0:
        print(f"  Cost: ${cost:.4f}")

    return output, cost


def run_modes_parallel(modes: list, question: str, with_clarification: bool = True) -> tuple[dict, dict, dict]:
    """Run all modes in parallel and return responses, costs, and metadata.

    If with_clarification=True, will retry any mode that appears to have
    misunderstood the question.
    """
    import time

    print("\n" + "="*60)
    print("RUNNING ALL MODES IN PARALLEL...")
    print("="*60)

    # Start all processes
    processes = {}
    start_time = time.time()

    for mode_key, mode_name, cmd in modes:
        print(f"  Starting {mode_name}...")
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        processes[mode_key] = (proc, mode_name, cmd)

    print(f"\n  Waiting for {len(processes)} processes...")

    # Collect initial results
    responses = {}
    costs = {}
    metadata = {}

    for mode_key, (proc, mode_name, cmd) in processes.items():
        try:
            stdout, stderr = proc.communicate(timeout=600)

            if proc.returncode != 0:
                responses[mode_key] = f"ERROR: {stderr}"
                costs[mode_key] = 0.0
                metadata[mode_key] = {"attempts": 1, "clarified": False, "error": True}
            else:
                responses[mode_key] = stdout

                # Extract cost
                cost = 0.0
                for line in stdout.split("\n"):
                    if "Cost:" in line and "$" in line:
                        try:
                            cost = float(line.split("$")[1].split()[0])
                        except (ValueError, IndexError):
                            pass
                costs[mode_key] = cost
                metadata[mode_key] = {"attempts": 1, "clarified": False}

            print(f"  {mode_name}: {len(responses[mode_key])} chars, ${costs[mode_key]:.4f}")

        except subprocess.TimeoutExpired:
            proc.kill()
            responses[mode_key] = "ERROR: Timeout after 10 minutes"
            costs[mode_key] = 0.0
            metadata[mode_key] = {"attempts": 1, "clarified": False, "timeout": True}
            print(f"  {mode_name}: TIMEOUT")

    elapsed = time.time() - start_time
    print(f"\n  Total parallel time: {elapsed:.1f}s")

    # Check for misunderstandings and retry if needed
    if with_clarification:
        retries_needed = []
        for mode_key, mode_name, cmd in modes:
            response = responses.get(mode_key, "")
            if is_empty_response(response):
                continue

            misunderstood, clarification = detect_misunderstanding(response, question)
            if misunderstood:
                retries_needed.append((mode_key, mode_name, cmd, clarification))

        if retries_needed:
            print(f"\n  Detected {len(retries_needed)} misunderstanding(s), retrying with clarification...")

            for mode_key, mode_name, cmd, clarification in retries_needed:
                print(f"\n  Retrying {mode_name}...")

                # Build clarified command
                clarified_question = f"{question}\n\n---\nCLARIFICATION: {clarification}"
                clarified_cmd = cmd.copy()
                for i, arg in enumerate(clarified_cmd):
                    if arg == question:
                        clarified_cmd[i] = clarified_question
                        break

                # Run retry
                response2, cost2 = run_mode_single(mode_key, f"{mode_name} (clarified)", clarified_cmd)

                # Update with clarified response
                original_len = len(responses[mode_key])
                responses[mode_key] = response2
                costs[mode_key] += cost2
                metadata[mode_key] = {
                    "attempts": 2,
                    "clarified": True,
                    "original_response_length": original_len,
                    "clarification_reason": clarification[:100],
                }
                print(f"    Clarified response: {len(response2)} chars, total cost: ${costs[mode_key]:.4f}")

    return responses, costs, metadata


def evaluate_response(response: str, mode_name: str) -> dict:
    """Evaluate a response using Claude as the judge."""
    if is_empty_response(response):
        return {
            "weighted_score": None,
            "overall": "No response or error",
            "empty_response": True,
        }

    judge_prompt = JUDGE_PROMPT_TEMPLATE.format(
        question=QUESTION,
        response=response[:12000]  # Allow more context for complex responses
    )

    print(f"  Evaluating {mode_name}...")

    cmd = ["minds", "ask", judge_prompt, "--model", "claude", "-y"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    except subprocess.TimeoutExpired:
        return {"error": "Judge timeout", "weighted_score": 0.0}

    if result.returncode != 0:
        return {"error": result.stderr, "weighted_score": 0.0}

    parsed = extract_json_from_output(result.stdout)
    if parsed:
        return parsed

    return {"error": "Failed to parse evaluation", "weighted_score": 0.0}


def main():
    import sys

    print("="*60)
    print("HARD QUESTION TEST - DISTRIBUTED CONSENSUS")
    print("="*60)
    print(f"\nQuestion:\n{QUESTION[:500]}...\n")

    # Check for cache
    responses_file = Path("hard_question_responses.json")
    use_cache = "--cache" in sys.argv and responses_file.exists()

    if use_cache:
        print("Loading cached responses...")
        cached = json.loads(responses_file.read_text())
        responses = cached["responses"]
        costs = cached["costs"]
        metadata = cached.get("metadata", {})
        for mode_key, mode_name, _ in MODES:
            r = responses.get(mode_key, "")
            c = costs.get(mode_key, 0)
            m = metadata.get(mode_key, {})
            clarified = " (clarified)" if m.get("clarified") else ""
            print(f"  {mode_name}{clarified}: {len(r)} chars, ${c:.4f}")
    else:
        # Run all modes in parallel (with automatic clarification retry)
        responses, costs, metadata = run_modes_parallel(MODES, QUESTION, with_clarification=True)

        # Save responses
        responses_file.write_text(json.dumps({
            "question": QUESTION,
            "responses": responses,
            "costs": costs,
            "metadata": metadata,
        }, indent=2))
        print(f"\nResponses saved to: {responses_file}")

    # Evaluate each response
    print("\n" + "="*60)
    print("EVALUATING RESPONSES (using Claude as judge)")
    print("="*60)

    evaluations = {}
    for mode_key, mode_name, _ in MODES:
        response = responses.get(mode_key, "")
        result = evaluate_response(response, mode_name)
        evaluations[mode_key] = result

        print(f"\n{mode_name.upper()}:")
        if result.get("empty_response"):
            print(f"  Score: N/A (no response)")
        elif "error" in result:
            print(f"  Error: {result.get('error', 'Unknown')[:100]}")
        else:
            ws = result.get("weighted_score", 0)
            print(f"  Weighted Score: {ws:.2f}" if isinstance(ws, (int, float)) else f"  Weighted Score: {ws}")
            print(f"  Overall: {result.get('overall', 'N/A')[:120]}")
            for criterion in ["technical_accuracy", "completeness", "reasoning_quality", "insight"]:
                if criterion in result:
                    score = result[criterion].get("score", "N/A")
                    print(f"    {criterion}: {score}")

    # Summary table
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)

    print("\n| Mode                    | Score | Tech | Comp | Reas | Ins  |")
    print("|-------------------------|-------|------|------|------|------|")

    results_list = []
    for mode_key, mode_name, _ in MODES:
        ev = evaluations[mode_key]
        score = ev.get("weighted_score")
        cost = costs.get(mode_key, 0)

        if score is None:
            print(f"| {mode_name:23} | N/A   | -    | -    | -    | -    |")
            results_list.append((mode_name, None, cost))
        else:
            if not isinstance(score, (int, float)):
                score = 0
            tech = ev.get("technical_accuracy", {}).get("score", "-")
            comp = ev.get("completeness", {}).get("score", "-")
            reas = ev.get("reasoning_quality", {}).get("score", "-")
            ins = ev.get("insight", {}).get("score", "-")
            print(f"| {mode_name:23} | {score:.2f}  | {tech}    | {comp}    | {reas}    | {ins}    |")
            results_list.append((mode_name, score, cost))

    # Rank by score
    print("\nRanked by Quality:")
    scored = [(n, s, c) for n, s, c in results_list if s is not None]
    for i, (name, score, cost) in enumerate(sorted(scored, key=lambda x: -x[1]), 1):
        cost_str = f"${cost:.2f}" if cost > 0 else "N/A"
        print(f"  {i}. {name}: {score:.2f} (cost: {cost_str})")

    # Show clarification summary
    clarified_modes = [k for k, m in metadata.items() if m.get("clarified")]
    if clarified_modes:
        print("\nClarification Summary:")
        for mode_key in clarified_modes:
            m = metadata[mode_key]
            mode_name = next((name for k, name, _ in MODES if k == mode_key), mode_key)
            print(f"  {mode_name}: Retried with clarification")
            print(f"    Reason: {m.get('clarification_reason', 'N/A')[:80]}...")

    # Save results
    results_file = Path("hard_question_results.json")
    results_file.write_text(json.dumps({
        "question": QUESTION,
        "costs": costs,
        "metadata": metadata,
        "evaluations": evaluations,
    }, indent=2))
    print(f"\nFull results saved to: {results_file}")


if __name__ == "__main__":
    main()

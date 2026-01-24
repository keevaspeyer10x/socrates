#!/usr/bin/env python3
"""Test script to compare minds modes using LLM-as-Judge evaluation.

Runs the same challenging question through:
1. minds (default - all top models)
2. minds --fast (fastest models)
3. minds --cheap (low-cost models)

Then evaluates each response using minds itself as the judge.
"""

import subprocess
import json
from pathlib import Path

# Challenging question that requires deep reasoning
QUESTION = """What are the second and third order effects of widespread AI coding assistants on the software industry over the next 5 years? Consider effects on:
- Junior developer career paths
- Code quality and technical debt
- Open source ecosystems
- Software security
- The economics of software development

Be specific about causal chains and identify potential feedback loops."""


JUDGE_PROMPT_TEMPLATE = """You are an expert evaluator assessing the quality of an AI-generated response.

## Evaluation Criteria (score 1-5 each):

1. **Depth** (30%): How thoroughly does the response explore the problem? Does it consider root causes, implications, and edge cases?
   - 1: Surface-level only
   - 3: Adequate depth
   - 5: Exceptional depth with subtle implications

2. **Coherence** (25%): Is the reasoning logically structured and internally consistent?
   - 1: Disjointed, contradictory
   - 3: Generally coherent
   - 5: Exceptionally clear logical flow

3. **Practicality** (25%): Are the conclusions actionable and grounded in reality?
   - 1: Impractical or ignores constraints
   - 3: Reasonably actionable
   - 5: Immediately actionable with clear steps

4. **Novelty** (20%): Does the response offer original insights or unexpected connections?
   - 1: Entirely conventional
   - 3: Some original thinking
   - 5: Highly original and insightful

## Question Asked:
{question}

## Response to Evaluate:
{response}

## Your Task:
Score this response on each criterion (1-5) and provide a brief justification. Then calculate the weighted score.

Respond in this exact JSON format:
```json
{{
  "depth": {{"score": <1-5>, "justification": "<brief reason>"}},
  "coherence": {{"score": <1-5>, "justification": "<brief reason>"}},
  "practicality": {{"score": <1-5>, "justification": "<brief reason>"}},
  "novelty": {{"score": <1-5>, "justification": "<brief reason>"}},
  "weighted_score": <calculated 0.0-1.0>,
  "overall": "<1-2 sentence summary>"
}}
```"""


COMPARE_PROMPT_TEMPLATE = """You are comparing two AI-generated responses to determine which is better.

## Question:
{question}

## Response A ({label_a}):
{response_a}

## Response B ({label_b}):
{response_b}

## Evaluation Criteria:
- Depth of analysis
- Logical coherence
- Practicality
- Originality of insights

## Your Task:
Compare these responses and determine which is better overall. Consider the quality of reasoning, not just length.

Respond in this exact JSON format:
```json
{{
  "winner": "<A or B or TIE>",
  "confidence": <0.0-1.0>,
  "explanation": "<1-2 sentence explanation>"
}}
```"""


def is_empty_response(response: str) -> bool:
    """Check if a response is empty/failed (just timeout errors, no actual content)."""
    # Check for common failure indicators
    if "Models: 0/" in response:
        return True
    if "timed out" in response.lower() and "Synthesis" not in response:
        return True
    # Check if there's a Synthesis section (indicates actual content)
    if "Synthesis" not in response and len(response) < 2000:
        return True
    return False


def run_minds(mode: str = "default") -> tuple[str, float]:
    """Run minds with specified mode and return response + cost."""
    cmd = ["minds", "ask", QUESTION, "-y"]

    if mode == "fast":
        cmd.append("--fast")
    elif mode == "cheap":
        cmd.append("--cheap")

    print(f"\n{'='*60}")
    print(f"Running minds --{mode}...")
    print(f"{'='*60}\n")

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        return f"ERROR: {result.stderr}", 0.0

    output = result.stdout

    # Extract cost from output
    cost = 0.0
    for line in output.split("\n"):
        if "Cost:" in line and "$" in line:
            try:
                cost = float(line.split("$")[1].split()[0])
            except (ValueError, IndexError):
                pass

    return output, cost


def extract_json_from_output(output: str) -> dict | None:
    """Extract JSON from minds output which may have rich formatting."""
    import re

    # Remove ANSI escape codes first
    clean = re.sub(r'\x1b\[[0-9;]*m', '', output)

    # Remove ALL unicode box drawing characters
    clean = re.sub(r'[\u2500-\u257F]', '', clean)  # Box drawing block
    clean = re.sub(r'[│╭╮╰╯┌┐└┘├┤┬┴┼]', '', clean)  # More box chars
    clean = re.sub(r'[⠀-⣿]', '', clean)  # Braille patterns (spinners)
    clean = re.sub(r'[✓✗]', '', clean)  # Check/X marks
    clean = re.sub(r'ⓘ', '', clean)  # Info symbol

    # Remove lines that are just whitespace or control chars
    lines = clean.split('\n')
    content_lines = []
    for line in lines:
        # Skip lines that look like the spinner/progress lines
        if re.match(r'^\s*(Asking|Claude|GPT|Gemini|Grok|DeepSeek|Total:)', line):
            continue
        # Skip empty/whitespace-only lines at start/end
        content_lines.append(line)

    clean = '\n'.join(content_lines)

    # Try to find JSON in code fence
    json_match = re.search(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```', clean)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    # Try to find standalone JSON object - greedy match for nested braces
    # Look for balanced braces
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
                # Try to parse this as JSON
                candidate = clean[start_idx:i+1]
                # Clean up any remaining whitespace issues
                candidate = re.sub(r'\s+', ' ', candidate)
                try:
                    return json.loads(candidate)
                except json.JSONDecodeError:
                    start_idx = None
                    continue

    return None


def evaluate_with_minds(question: str, response: str, mode_name: str) -> dict:
    """Evaluate a response using minds as the judge."""
    judge_prompt = JUDGE_PROMPT_TEMPLATE.format(
        question=question,
        response=response[:8000]  # Truncate to avoid token limits
    )

    print(f"\nEvaluating {mode_name} response with minds...")

    # Use single model for judging to be consistent
    cmd = ["minds", "ask", judge_prompt, "-1", "-y"]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

    if result.returncode != 0:
        return {"error": result.stderr, "weighted_score": 0.0}

    output = result.stdout

    parsed = extract_json_from_output(output)
    if parsed:
        return parsed

    return {"error": "Failed to parse evaluation", "weighted_score": 0.0, "raw": output[:500]}


def compare_with_minds(question: str, response_a: str, response_b: str, label_a: str, label_b: str) -> dict:
    """Compare two responses using minds."""
    compare_prompt = COMPARE_PROMPT_TEMPLATE.format(
        question=question,
        response_a=response_a[:4000],
        response_b=response_b[:4000],
        label_a=label_a,
        label_b=label_b,
    )

    print(f"\nComparing {label_a} vs {label_b}...")

    cmd = ["minds", "ask", compare_prompt, "-1", "-y"]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

    if result.returncode != 0:
        return {"error": result.stderr, "winner": "TIE"}

    output = result.stdout

    parsed = extract_json_from_output(output)
    if parsed:
        return parsed

    return {"error": "Failed to parse comparison", "winner": "TIE", "raw": output[:500]}


def main():
    import sys

    print("="*60)
    print("MINDS MODE COMPARISON TEST")
    print("="*60)
    print(f"\nQuestion:\n{QUESTION}\n")

    # Check if we should reload from cache
    responses_file = Path("minds_comparison_responses.json")
    use_cache = "--cache" in sys.argv and responses_file.exists()

    if use_cache:
        print("Loading cached responses...")
        cached = json.loads(responses_file.read_text())
        responses = cached["responses"]
        costs = cached["costs"]
        for mode in ["default", "fast", "cheap"]:
            print(f"  {mode}: {len(responses[mode])} chars, ${costs[mode]:.4f}")
    else:
        # Collect responses from each mode
        responses = {}
        costs = {}

        for mode in ["default", "fast", "cheap"]:
            response, cost = run_minds(mode)
            responses[mode] = response
            costs[mode] = cost
            print(f"\n{mode} cost: ${cost:.4f}")
            print(f"{mode} response length: {len(response)} chars")

        # Save responses
        responses_file.write_text(json.dumps({
            "question": QUESTION,
            "responses": responses,
            "costs": costs,
        }, indent=2))
        print(f"\nResponses saved to: {responses_file}")

    # Run evaluations
    print("\n" + "="*60)
    print("EVALUATING RESPONSES (using Claude as judge)")
    print("="*60)

    evaluations = {}
    for mode, response in responses.items():
        # Check if response is empty/failed
        if is_empty_response(response):
            evaluations[mode] = {
                "weighted_score": None,
                "overall": "No response - all models timed out or failed",
                "empty_response": True,
            }
            print(f"\n{mode.upper()} EVALUATION:")
            print(f"  Weighted Score: N/A (no response)")
            print(f"  Overall: All models timed out or failed")
            continue

        result = evaluate_with_minds(QUESTION, response, mode)
        evaluations[mode] = result

        print(f"\n{mode.upper()} EVALUATION:")
        if "error" in result:
            print(f"  Error: {result.get('error', 'Unknown')[:100]}")
        else:
            ws = result.get("weighted_score", 0)
            print(f"  Weighted Score: {ws:.2f}" if isinstance(ws, (int, float)) else f"  Weighted Score: {ws}")
            print(f"  Overall: {result.get('overall', 'N/A')[:100]}")
            for criterion in ["depth", "coherence", "practicality", "novelty"]:
                if criterion in result:
                    score = result[criterion].get("score", "N/A")
                    print(f"    {criterion}: {score}")

    # Pairwise comparisons
    print("\n" + "="*60)
    print("PAIRWISE COMPARISONS")
    print("="*60)

    comparisons = []
    modes = ["default", "fast", "cheap"]

    for i in range(len(modes)):
        for j in range(i + 1, len(modes)):
            mode_a, mode_b = modes[i], modes[j]

            # Check if either response is empty
            a_empty = is_empty_response(responses[mode_a])
            b_empty = is_empty_response(responses[mode_b])

            if a_empty and b_empty:
                result = {"winner": "TIE", "confidence": 1.0, "explanation": "Both modes failed to produce responses"}
            elif a_empty:
                result = {"winner": "B", "confidence": 1.0, "explanation": f"{mode_a} failed to produce a response"}
            elif b_empty:
                result = {"winner": "A", "confidence": 1.0, "explanation": f"{mode_b} failed to produce a response"}
            else:
                result = compare_with_minds(
                    QUESTION,
                    responses[mode_a],
                    responses[mode_b],
                    mode_a,
                    mode_b,
                )

            comparisons.append({
                "pair": f"{mode_a} vs {mode_b}",
                **result
            })

            print(f"\n{mode_a} vs {mode_b}:")
            winner = result.get("winner", "TIE")
            # Map A/B back to mode names
            if winner == "A":
                winner = mode_a
            elif winner == "B":
                winner = mode_b
            print(f"  Winner: {winner}")
            print(f"  Confidence: {result.get('confidence', 'N/A')}")
            print(f"  Reason: {result.get('explanation', 'N/A')[:100]}...")

    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)

    print("\n| Mode    | Score | Cost    | Score/$ |")
    print("|---------|-------|---------|---------|")
    for mode in ["default", "fast", "cheap"]:
        score = evaluations[mode].get("weighted_score")
        cost = costs[mode]
        if score is None:
            print(f"| {mode:7} | N/A   | ${cost:.4f} | N/A     |")
        else:
            if not isinstance(score, (int, float)):
                score = 0
            efficiency = score / cost if cost > 0 else 0
            print(f"| {mode:7} | {score:.2f}  | ${cost:.4f} | {efficiency:.1f}     |")

    # Win tally
    print("\nPairwise Win Tally:")
    wins = {m: 0 for m in modes}
    for comp in comparisons:
        winner = comp.get("winner", "TIE")
        pair = comp["pair"]
        mode_a, mode_b = pair.split(" vs ")
        if winner == "A":
            wins[mode_a] += 1
        elif winner == "B":
            wins[mode_b] += 1

    for mode in modes:
        print(f"  {mode}: {wins[mode]} wins")

    # Save full results
    results_file = Path("minds_comparison_results.json")
    results_file.write_text(json.dumps({
        "question": QUESTION,
        "costs": costs,
        "evaluations": evaluations,
        "comparisons": comparisons,
    }, indent=2))
    print(f"\nFull results saved to: {results_file}")


if __name__ == "__main__":
    main()

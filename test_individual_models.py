#!/usr/bin/env python3
"""Test each SOTA model individually on the same question and evaluate with LLM-as-Judge."""

import subprocess
import json
from pathlib import Path
import re

# The same challenging question
QUESTION = """What are the second and third order effects of widespread AI coding assistants on the software industry over the next 5 years? Consider effects on:
- Junior developer career paths
- Code quality and technical debt
- Open source ecosystems
- Software security
- The economics of software development

Be specific about causal chains and identify potential feedback loops."""

# The 5 SOTA models
MODELS = [
    ("claude", "Claude Opus 4.5"),
    ("gemini", "Gemini 3 Pro"),
    ("gpt", "GPT-5.2"),
    ("grok", "Grok 4.1"),
    ("deepseek", "DeepSeek V3.2"),
]

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


def extract_json_from_output(output: str) -> dict | None:
    """Extract JSON from minds output which may have rich formatting."""
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
        content_lines.append(line)

    clean = '\n'.join(content_lines)

    # Try to find JSON in code fence
    json_match = re.search(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```', clean)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    # Try to find standalone JSON object - balanced braces
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


def run_model(model_key: str, model_name: str) -> tuple[str, float]:
    """Run a single model and return response + cost."""
    cmd = ["minds", "ask", QUESTION, "--model", model_key, "-y"]

    print(f"\n{'='*60}")
    print(f"Querying {model_name}...")
    print(f"{'='*60}")

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)

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


def is_empty_response(response: str) -> bool:
    """Check if a response is empty/failed."""
    if "ERROR:" in response:
        return True
    if "timed out" in response.lower():
        return True
    # Check for actual content - should have some substantial text
    clean = re.sub(r'[\u2500-\u257F│╭╮╰╯]', '', response)
    clean = re.sub(r'\x1b\[[0-9;]*m', '', clean)
    if len(clean.strip()) < 500:
        return True
    return False


def evaluate_response(response: str, model_name: str) -> dict:
    """Evaluate a response using Claude as the judge."""
    if is_empty_response(response):
        return {
            "weighted_score": None,
            "overall": "No response or error",
            "empty_response": True,
        }

    judge_prompt = JUDGE_PROMPT_TEMPLATE.format(
        question=QUESTION,
        response=response[:8000]
    )

    print(f"  Evaluating {model_name} response...")

    # Use Claude as judge
    cmd = ["minds", "ask", judge_prompt, "--model", "claude", "-y"]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

    if result.returncode != 0:
        return {"error": result.stderr, "weighted_score": 0.0}

    parsed = extract_json_from_output(result.stdout)
    if parsed:
        return parsed

    return {"error": "Failed to parse evaluation", "weighted_score": 0.0}


def main():
    import sys

    print("="*60)
    print("INDIVIDUAL MODEL COMPARISON TEST")
    print("="*60)
    print(f"\nQuestion:\n{QUESTION}\n")

    # Check for cache
    responses_file = Path("individual_model_responses.json")
    use_cache = "--cache" in sys.argv and responses_file.exists()

    if use_cache:
        print("Loading cached responses...")
        cached = json.loads(responses_file.read_text())
        responses = cached["responses"]
        costs = cached["costs"]
        for model_key, model_name in MODELS:
            print(f"  {model_name}: {len(responses.get(model_key, ''))} chars, ${costs.get(model_key, 0):.4f}")
    else:
        # Query each model
        responses = {}
        costs = {}

        for model_key, model_name in MODELS:
            response, cost = run_model(model_key, model_name)
            responses[model_key] = response
            costs[model_key] = cost
            print(f"  Cost: ${cost:.4f}")
            print(f"  Response length: {len(response)} chars")

        # Save responses
        responses_file.write_text(json.dumps({
            "question": QUESTION,
            "responses": responses,
            "costs": costs,
        }, indent=2))
        print(f"\nResponses saved to: {responses_file}")

    # Evaluate each response
    print("\n" + "="*60)
    print("EVALUATING RESPONSES (using Claude as judge)")
    print("="*60)

    evaluations = {}
    for model_key, model_name in MODELS:
        response = responses.get(model_key, "")
        result = evaluate_response(response, model_name)
        evaluations[model_key] = result

        print(f"\n{model_name.upper()}:")
        if result.get("empty_response"):
            print(f"  Score: N/A (no response)")
        elif "error" in result:
            print(f"  Error: {result.get('error', 'Unknown')[:100]}")
        else:
            ws = result.get("weighted_score", 0)
            print(f"  Weighted Score: {ws:.2f}" if isinstance(ws, (int, float)) else f"  Weighted Score: {ws}")
            print(f"  Overall: {result.get('overall', 'N/A')[:100]}")
            for criterion in ["depth", "coherence", "practicality", "novelty"]:
                if criterion in result:
                    score = result[criterion].get("score", "N/A")
                    print(f"    {criterion}: {score}")

    # Summary table
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)

    print("\n| Model           | Score | Cost    | Score/$ |")
    print("|-----------------|-------|---------|---------|")

    results_list = []
    for model_key, model_name in MODELS:
        score = evaluations[model_key].get("weighted_score")
        cost = costs.get(model_key, 0)

        if score is None:
            print(f"| {model_name:15} | N/A   | ${cost:.4f} | N/A     |")
            results_list.append((model_name, None, cost, None))
        else:
            if not isinstance(score, (int, float)):
                score = 0
            efficiency = score / cost if cost > 0 else float('inf')
            print(f"| {model_name:15} | {score:.2f}  | ${cost:.4f} | {efficiency:.1f}     |")
            results_list.append((model_name, score, cost, efficiency))

    # Rank by score
    print("\nRanked by Quality:")
    scored = [(n, s, c) for n, s, c, _ in results_list if s is not None]
    for i, (name, score, cost) in enumerate(sorted(scored, key=lambda x: -x[1]), 1):
        print(f"  {i}. {name}: {score:.2f}")

    # Rank by efficiency
    print("\nRanked by Value (Score/$):")
    efficient = [(n, s, c, e) for n, s, c, e in results_list if e is not None]
    for i, (name, score, cost, eff) in enumerate(sorted(efficient, key=lambda x: -x[3]), 1):
        print(f"  {i}. {name}: {eff:.1f} (${cost:.4f})")

    # Save results
    results_file = Path("individual_model_results.json")
    results_file.write_text(json.dumps({
        "question": QUESTION,
        "costs": costs,
        "evaluations": evaluations,
    }, indent=2))
    print(f"\nFull results saved to: {results_file}")


if __name__ == "__main__":
    main()

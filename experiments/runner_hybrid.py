#!/usr/bin/env python3
"""
Hybrid Verification Runner - Dynamic routing based on question type.

Based on Phase 2A experiment findings:
- Factual questions: generic_critique performs best (8.0 adversarial)
- Reasoning questions: reasoning_verification performs best (8.0 adversarial, 8.1 reasoning)
- Contested questions: reasoning_verification slightly better (7.4 adversarial)

This runner:
1. Classifies question type using LLM
2. Routes to appropriate verification method
3. Compares dynamic routing vs fixed methods

Usage:
    python3 experiments/runner_hybrid.py           # Run experiments
    python3 experiments/runner_hybrid.py --analyze # Analyze only
"""

import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# Configuration
EXPERIMENTS_DIR = Path(__file__).parent
STATE_FILE = EXPERIMENTS_DIR / "experiment_state_hybrid.json"
LOG_FILE = EXPERIMENTS_DIR / "experiment_hybrid.log"
RESULTS_FILE = EXPERIMENTS_DIR / "experiment_results_hybrid.json"
BUDGET_LIMIT = 30.0
RETRY_DELAY = 5
MAX_RETRIES = 3
SEEDS_PER_QUESTION = 2

# Same questions as v2 for comparison
QUESTIONS = {
    # === FACTUAL-HARD ===
    "factual_hard_1": {
        "type": "factual",
        "question": "Summarize Justice Sotomayor's dissent in Vara v. TechGlobal (2022), focusing on her arguments about algorithmic accountability.",
        "notes": "Case doesn't exist - tests hallucination detection",
        "ground_truth": "This case does not exist"
    },
    "factual_hard_2": {
        "type": "factual",
        "question": "What percentage of Fortune 500 CEOs have Harvard MBAs specifically? Cite your source.",
        "notes": "Commonly fabricated statistic - tests citation accuracy",
        "ground_truth": "Should acknowledge uncertainty or cite real source"
    },
    "factual_hard_3": {
        "type": "factual",
        "question": "List three chemicals that were banned under the 1987 Stockholm Convention on Persistent Organic Pollutants.",
        "notes": "Stockholm Convention is 2001, not 1987 - tests temporal accuracy",
        "ground_truth": "Should note Stockholm Convention is 2001, not 1987"
    },
    "factual_hard_4": {
        "type": "factual",
        "question": "What was the exact cost per mile of California High-Speed Rail Phase 1 construction as of 2023, and how does it compare to Japan's Shinkansen extensions?",
        "notes": "Precise figures often fabricated - tests numeric accuracy",
        "ground_truth": "Should acknowledge figures are estimates/contested"
    },

    # === REASONING-HARD ===
    "reasoning_hard_1": {
        "type": "reasoning",
        "question": "A bat and ball cost $1.10 together. The bat costs $1.00 more than the ball. How much does the ball cost? Show your work step by step.",
        "notes": "Classic cognitive bias trap - answer is $0.05, not $0.10",
        "ground_truth": "$0.05"
    },
    "reasoning_hard_2": {
        "type": "reasoning",
        "question": "You have 12 coins, one of which is counterfeit (either heavier or lighter than the rest). Using a balance scale exactly 3 times, how would you identify the counterfeit coin AND determine whether it's heavier or lighter?",
        "notes": "Complex constraint satisfaction",
        "ground_truth": "Valid algorithm that works in all cases"
    },
    "reasoning_hard_3": {
        "type": "reasoning",
        "question": "Three people check into a hotel room that costs $30. They each pay $10. Later, the clerk realizes the room was only $25 and gives $5 to the bellhop to return. The bellhop keeps $2 and gives $1 back to each person. Now each person paid $9 (total $27), plus the bellhop has $2, equals $29. Where's the missing dollar?",
        "notes": "Classic misdirection puzzle",
        "ground_truth": "The framing is wrong - $27 includes the $2, shouldn't add them"
    },
    "reasoning_hard_4": {
        "type": "reasoning",
        "question": "A snail is at the bottom of a 30-foot well. Each day it climbs up 3 feet, but each night it slides back down 2 feet. On which day does the snail reach the top of the well?",
        "notes": "Edge case reasoning - answer is day 28, not day 30",
        "ground_truth": "Day 28"
    },

    # === CONTESTED ===
    "contested_1": {
        "type": "contested",
        "question": "Should a 50-person engineering team at a growth-stage startup migrate from a Django monolith to microservices? They're experiencing scaling issues but have limited DevOps expertise. Take a clear position with reasoning.",
        "notes": "Architectural decision",
        "ground_truth": None
    },
    "contested_2": {
        "type": "contested",
        "question": "Is remote work better for company culture long-term compared to in-office work? Consider a 200-person tech company. Take a position and defend it.",
        "notes": "Contested topic",
        "ground_truth": None
    },
    "contested_3": {
        "type": "contested",
        "question": "Should AI companies be required to open-source their large language models for safety research? Argue one side with specific reasoning.",
        "notes": "Policy question",
        "ground_truth": None
    },
    "contested_4": {
        "type": "contested",
        "question": "What explains the productivity paradox - why hasn't AI visibly boosted economic productivity statistics despite widespread adoption? Provide a clear thesis with supporting arguments.",
        "notes": "Analytical question",
        "ground_truth": None
    },
}

# Methods to compare
METHODS = {
    "hybrid_routing": {
        "description": "Dynamic routing: classify then apply best method",
        "type": "hybrid"
    },
    "always_critique": {
        "description": "Always use generic_critique",
        "type": "fixed"
    },
    "always_reasoning": {
        "description": "Always use reasoning_verification",
        "type": "fixed"
    },
    "gpt_baseline": {
        "description": "GPT single-shot (reference)",
        "type": "baseline"
    },
}

# Routing rules based on Phase 2A findings
ROUTING_RULES = {
    "factual": "generic_critique",      # 8.0 adversarial on factual
    "reasoning": "reasoning_verification",  # 9.0 adversarial on reasoning
    "contested": "reasoning_verification",  # 7.4 adversarial on contested
}


def log(message: str, level: str = "INFO"):
    """Append to log file and print."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] [{level}] {message}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")


def load_state() -> dict:
    """Load state from checkpoint or initialize."""
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            state = json.load(f)
        done = sum(1 for r in state['runs'].values() if r.get('generation', {}).get('done'))
        log(f"Loaded state: ${state['total_cost']:.4f} spent, {done} generations done")
        return state

    state = {
        "total_cost": 0.0,
        "total_tokens": 0,
        "budget_limit": BUDGET_LIMIT,
        "started_at": datetime.now().isoformat(),
        "runs": {}
    }

    for q_id in QUESTIONS:
        for m_id in METHODS:
            for seed in range(SEEDS_PER_QUESTION):
                run_id = f"{m_id}__{q_id}__seed{seed}"
                state["runs"][run_id] = {
                    "question_id": q_id,
                    "method_id": m_id,
                    "seed": seed,
                    "generation": {"done": False, "response": None, "cost": 0.0, "tokens": 0},
                    "judge": {"done": False, "scores": None, "cost": 0.0}
                }

    save_state(state)
    log(f"Initialized state with {len(state['runs'])} runs")
    return state


def save_state(state: dict):
    """Atomic save to state file."""
    state["last_updated"] = datetime.now().isoformat()
    tmp_file = STATE_FILE.with_suffix(".tmp")
    with open(tmp_file, "w") as f:
        json.dump(state, f, indent=2)
    os.replace(tmp_file, STATE_FILE)


def parse_cost_and_tokens(output: str) -> tuple[float, int]:
    """Extract cost and estimate tokens from minds CLI output."""
    cost = 0.0
    tokens = 0

    match = re.search(r'Total:.*\|\s*Cost:\s*\$?([\d.]+)\s*\|', output)
    if match:
        cost = float(match.group(1))
        if cost > 1.0:
            cost = 0.0

    tokens = len(output) // 4
    return cost, tokens


def call_single_model(prompt: str, model: str = "gpt", timeout: int = 120) -> tuple[str, float, int]:
    """Call minds with a single model."""
    cmd = ["minds", "ask", "--model", model, "--yes", prompt]

    for attempt in range(MAX_RETRIES):
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            full_output = result.stdout + result.stderr
            cost, tokens = parse_cost_and_tokens(full_output)
            response = result.stdout.strip()

            if response:
                return response, cost, tokens
            else:
                log(f"Empty response on attempt {attempt + 1}", "WARN")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY)
        except subprocess.TimeoutExpired:
            log(f"Timeout on attempt {attempt + 1}/{MAX_RETRIES}", "WARN")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY * (attempt + 1))
        except Exception as e:
            log(f"Single model error: {e}", "ERROR")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)

    return "", 0.0, 0


# ============ CLASSIFICATION ============

def classify_question(question: str) -> tuple[str, float, int]:
    """Classify question type using LLM."""
    classify_prompt = f"""Classify this question into exactly one category.

Question: {question}

Categories:
- FACTUAL: Questions about facts, statistics, historical events, citations
- REASONING: Logic puzzles, math problems, step-by-step deduction required
- CONTESTED: Policy debates, architectural decisions, opinions, no single right answer

Output only one word: FACTUAL, REASONING, or CONTESTED"""

    response, cost, tokens = call_single_model(classify_prompt, model="gpt", timeout=60)

    # Parse classification
    response_upper = response.upper().strip()
    if "FACTUAL" in response_upper:
        return "factual", cost, tokens
    elif "REASONING" in response_upper:
        return "reasoning", cost, tokens
    elif "CONTESTED" in response_upper:
        return "contested", cost, tokens
    else:
        # Default to reasoning if unclear
        log(f"Unclear classification '{response}', defaulting to reasoning", "WARN")
        return "reasoning", cost, tokens


# ============ VERIFICATION METHODS ============

def run_gpt_baseline(question: str) -> tuple[str, float, int, list]:
    """GPT single-shot baseline."""
    response, cost, tokens = call_single_model(question, model="gpt")
    return response, cost, tokens, []


def run_generic_critique(question: str) -> tuple[str, float, int, list]:
    """Generate -> Critique -> Revise."""
    intermediates = []
    total_cost, total_tokens = 0.0, 0

    # Step 1: Generate
    response, cost, tokens = call_single_model(question, model="gpt")
    intermediates.append({"step": "initial", "response": response[:500]})
    total_cost += cost
    total_tokens += tokens

    # Step 2: Critique
    critique_prompt = f"""Critically evaluate this response. Find any errors, unsupported claims, logical gaps, or issues.

Question: {question}

Response to critique:
{response}

Provide a detailed critique."""

    critique, cost, tokens = call_single_model(critique_prompt, model="gpt")
    intermediates.append({"step": "critique", "response": critique[:500]})
    total_cost += cost
    total_tokens += tokens

    # Step 3: Revise
    revise_prompt = f"""Revise your answer based on this critique.

Original question: {question}

Original response:
{response}

Critique:
{critique}

Provide an improved response that addresses the critique."""

    final_response, cost, tokens = call_single_model(revise_prompt, model="gpt")
    total_cost += cost
    total_tokens += tokens

    return final_response, total_cost, total_tokens, intermediates


def run_reasoning_verification(question: str) -> tuple[str, float, int, list]:
    """Explicit logic checking."""
    intermediates = []
    total_cost, total_tokens = 0.0, 0

    # Step 1: Generate with explicit reasoning
    reason_prompt = f"""Answer this question with explicit step-by-step reasoning. Number each logical step.

{question}"""

    response, cost, tokens = call_single_model(reason_prompt, model="gpt")
    intermediates.append({"step": "initial", "response": response[:500]})
    total_cost += cost
    total_tokens += tokens

    # Step 2: Verify reasoning steps
    verify_prompt = f"""Check each reasoning step in this response for logical validity.

For each step:
1. Identify the premise and conclusion
2. Check if the conclusion follows from the premise
3. Flag any logical fallacies
4. Check if any step depends on an unsupported assumption

Question: {question}

Response to verify:
{response}

Provide your step-by-step verification."""

    verification, cost, tokens = call_single_model(verify_prompt, model="gpt")
    intermediates.append({"step": "verification", "response": verification[:500]})
    total_cost += cost
    total_tokens += tokens

    # Step 3: Revise
    revise_prompt = f"""Revise your answer based on the logical verification.

Original question: {question}

Original response:
{response}

Logical verification:
{verification}

Provide a revised response that fixes any logical issues identified."""

    final_response, cost, tokens = call_single_model(revise_prompt, model="gpt")
    total_cost += cost
    total_tokens += tokens

    return final_response, total_cost, total_tokens, intermediates


def run_hybrid_routing(question: str) -> tuple[str, float, int, list]:
    """Classify question type, then route to best method."""
    intermediates = []
    total_cost, total_tokens = 0.0, 0

    # Step 1: Classify
    question_type, cost, tokens = classify_question(question)
    intermediates.append({"step": "classification", "type": question_type})
    total_cost += cost
    total_tokens += tokens

    # Step 2: Route to appropriate method
    method = ROUTING_RULES[question_type]
    log(f"    Classified as {question_type} -> routing to {method}")

    if method == "generic_critique":
        response, cost, tokens, sub_intermediates = run_generic_critique(question)
    else:  # reasoning_verification
        response, cost, tokens, sub_intermediates = run_reasoning_verification(question)

    intermediates.extend(sub_intermediates)
    total_cost += cost
    total_tokens += tokens

    return response, total_cost, total_tokens, intermediates


METHOD_RUNNERS = {
    "hybrid_routing": run_hybrid_routing,
    "always_critique": run_generic_critique,
    "always_reasoning": run_reasoning_verification,
    "gpt_baseline": run_gpt_baseline,
}


# ============ JUDGE EVALUATION ============

def run_judge(question: str, response: str, question_type: str, ground_truth: str = None) -> tuple[dict, float]:
    """Run LLM-as-judge evaluation."""

    ground_truth_section = ""
    if ground_truth:
        ground_truth_section = f"\n\nGround truth (for factual/reasoning questions): {ground_truth}"

    judge_prompt = f"""Evaluate this response on three dimensions. Be critical and specific.

Question: {question}
Question type: {question_type}{ground_truth_section}

Response to evaluate:
{response}

**Evaluation Criteria:**

1. **Style Score (0-10)**: Depth, specificity, actionability, clarity
2. **Adversarial Score (0-10)**: Would this survive fact-checking?
3. **Reasoning Score (0-10)**: Logical structure and validity
4. **Verification Breakdown (yes/no)**: Did the response get WORSE than a simple direct answer would?

Output format:
STYLE_SCORE: [0-10]
ADVERSARIAL_SCORE: [0-10]
REASONING_SCORE: [0-10]
VERIFICATION_BREAKDOWN: [yes/no]
BRIEF_JUSTIFICATION: [2-3 sentences]"""

    result, cost, _ = call_single_model(judge_prompt, model="gpt", timeout=120)

    scores = {}
    for metric in ["STYLE", "ADVERSARIAL", "REASONING"]:
        match = re.search(rf'{metric}_SCORE:\s*(\d+)', result)
        scores[metric.lower()] = int(match.group(1)) if match else None

    match = re.search(r'VERIFICATION_BREAKDOWN:\s*(yes|no)', result, re.IGNORECASE)
    scores["verification_breakdown"] = match.group(1).lower() == "yes" if match else None

    match = re.search(r'BRIEF_JUSTIFICATION:\s*(.+?)$', result, re.DOTALL)
    scores["justification"] = match.group(1).strip()[:300] if match else None

    return scores, cost


# ============ MAIN EXECUTION ============

def run_generation_phase(state: dict) -> dict:
    """Run all generations."""
    log("=" * 60)
    log("STARTING GENERATION PHASE (HYBRID)")
    log("=" * 60)

    pending = [
        (run_id, run)
        for run_id, run in state["runs"].items()
        if not run["generation"]["done"]
    ]

    log(f"{len(pending)} generations pending")

    for i, (run_id, run) in enumerate(pending):
        if state["total_cost"] >= state["budget_limit"]:
            log(f"BUDGET LIMIT REACHED: ${state['total_cost']:.4f}", "WARN")
            break

        q_id = run["question_id"]
        m_id = run["method_id"]
        seed = run["seed"]
        question = QUESTIONS[q_id]["question"]

        log(f"[{i+1}/{len(pending)}] Running {m_id} on {q_id} (seed {seed})...")

        start_time = time.time()

        try:
            runner = METHOD_RUNNERS[m_id]
            response, cost, tokens, intermediates = runner(question)

            elapsed = time.time() - start_time

            run["generation"] = {
                "done": True,
                "response": response,
                "cost": cost,
                "tokens": tokens,
                "intermediate": intermediates,
                "elapsed_seconds": elapsed
            }

            state["total_cost"] += cost
            state["total_tokens"] += tokens
            save_state(state)

            log(f"  Done in {elapsed:.1f}s, cost: ${cost:.4f}, ~{tokens} tokens")

        except Exception as e:
            log(f"  ERROR: {e}", "ERROR")
            run["generation"]["error"] = str(e)
            save_state(state)

        time.sleep(2)

    return state


def run_judge_phase(state: dict) -> dict:
    """Run all judge evaluations."""
    log("=" * 60)
    log("STARTING JUDGE PHASE")
    log("=" * 60)

    pending = [
        (run_id, run)
        for run_id, run in state["runs"].items()
        if run["generation"]["done"] and not run["judge"]["done"]
    ]

    log(f"{len(pending)} judge evaluations pending")

    for i, (run_id, run) in enumerate(pending):
        if state["total_cost"] >= state["budget_limit"]:
            log(f"BUDGET LIMIT REACHED: ${state['total_cost']:.4f}", "WARN")
            break

        q_id = run["question_id"]
        question = QUESTIONS[q_id]["question"]
        question_type = QUESTIONS[q_id]["type"]
        ground_truth = QUESTIONS[q_id].get("ground_truth")
        response = run["generation"]["response"]

        log(f"[{i+1}/{len(pending)}] Judging {run_id}...")

        try:
            scores, cost = run_judge(question, response, question_type, ground_truth)

            run["judge"] = {
                "done": True,
                "scores": scores,
                "cost": cost
            }

            state["total_cost"] += cost
            save_state(state)

            style = scores.get("style", "?")
            adv = scores.get("adversarial", "?")
            reason = scores.get("reasoning", "?")
            breakdown = "BREAKDOWN" if scores.get("verification_breakdown") else ""
            log(f"  S:{style} A:{adv} R:{reason} {breakdown}")

        except Exception as e:
            log(f"  ERROR: {e}", "ERROR")
            run["judge"]["error"] = str(e)
            save_state(state)

        time.sleep(1)

    return state


def analyze_results(state: dict):
    """Analyze results comparing hybrid vs fixed methods."""
    log("=" * 60)
    log("ANALYZING HYBRID RESULTS")
    log("=" * 60)

    results = {
        "by_method": {},
        "by_question_type": {},
        "routing_accuracy": {},  # Did hybrid route correctly?
        "total_cost": state["total_cost"],
        "total_tokens": state.get("total_tokens", 0)
    }

    # Collect all scores
    for run_id, run in state["runs"].items():
        if not run["judge"]["done"]:
            continue

        m_id = run["method_id"]
        q_id = run["question_id"]
        q_type = QUESTIONS[q_id]["type"]
        scores = run["judge"]["scores"]
        gen = run["generation"]

        # By method
        if m_id not in results["by_method"]:
            results["by_method"][m_id] = {
                "style": [], "adversarial": [], "reasoning": [],
                "tokens": [], "breakdowns": 0
            }

        for metric in ["style", "adversarial", "reasoning"]:
            if scores.get(metric) is not None:
                results["by_method"][m_id][metric].append(scores[metric])

        results["by_method"][m_id]["tokens"].append(gen.get("tokens", 0))
        if scores.get("verification_breakdown"):
            results["by_method"][m_id]["breakdowns"] += 1

        # Track hybrid routing decisions
        if m_id == "hybrid_routing" and gen.get("intermediate"):
            classification = next(
                (i for i in gen["intermediate"] if i.get("step") == "classification"),
                None
            )
            if classification:
                classified_type = classification.get("type")
                actual_type = q_type

                if actual_type not in results["routing_accuracy"]:
                    results["routing_accuracy"][actual_type] = {"correct": 0, "total": 0}

                results["routing_accuracy"][actual_type]["total"] += 1
                if classified_type == actual_type:
                    results["routing_accuracy"][actual_type]["correct"] += 1

    # Print results
    log("\n=== RESULTS BY METHOD ===")
    log(f"{'Method':<18} | {'Style':^7} | {'Adv':^7} | {'Reason':^7} | {'Tokens':^8} | {'Breakdowns':^10}")
    log("-" * 75)

    for m_id, data in sorted(results["by_method"].items(),
                             key=lambda x: sum(x[1].get("adversarial", [0]))/max(len(x[1].get("adversarial", [1])),1),
                             reverse=True):
        avg_s = sum(data["style"])/len(data["style"]) if data["style"] else 0
        avg_a = sum(data["adversarial"])/len(data["adversarial"]) if data["adversarial"] else 0
        avg_r = sum(data["reasoning"])/len(data["reasoning"]) if data["reasoning"] else 0
        avg_tokens = sum(data["tokens"])/len(data["tokens"]) if data["tokens"] else 0
        breakdowns = data["breakdowns"]
        n = len(data["style"])

        data["avg_style"] = avg_s
        data["avg_adversarial"] = avg_a
        data["avg_reasoning"] = avg_r
        data["avg_tokens"] = avg_tokens
        data["n"] = n

        log(f"{m_id:<18} | {avg_s:>5.1f}  | {avg_a:>5.1f}  | {avg_r:>5.1f}  | {avg_tokens:>7.0f} | {breakdowns}/{n}")

    # Routing accuracy
    if results["routing_accuracy"]:
        log("\n=== ROUTING ACCURACY ===")
        for q_type, counts in results["routing_accuracy"].items():
            accuracy = counts["correct"] / counts["total"] * 100 if counts["total"] > 0 else 0
            log(f"{q_type}: {counts['correct']}/{counts['total']} ({accuracy:.0f}%)")

    # Win rate analysis
    log("\n=== WIN RATE ANALYSIS ===")
    # Compare hybrid vs always_critique and always_reasoning
    methods_to_compare = ["hybrid_routing", "always_critique", "always_reasoning"]

    for method in methods_to_compare:
        if method in results["by_method"]:
            data = results["by_method"][method]
            log(f"{method}: avg adversarial = {data.get('avg_adversarial', 0):.2f}")

    log(f"\n=== SUMMARY ===")
    log(f"Total cost: ${state['total_cost']:.4f}")
    log(f"Total tokens: ~{state.get('total_tokens', 0):,}")

    with open(RESULTS_FILE, "w") as f:
        json.dump(results, f, indent=2)

    log(f"Results saved to {RESULTS_FILE}")
    return results


def main():
    """Main entry point."""
    log("=" * 60)
    log("HYBRID VERIFICATION RUNNER STARTED")
    log(f"State file: {STATE_FILE}")
    log(f"Budget limit: ${BUDGET_LIMIT}")
    log("=" * 60)

    analyze_only = "--analyze" in sys.argv

    state = load_state()

    if analyze_only:
        analyze_results(state)
        return

    state = run_generation_phase(state)
    state = run_judge_phase(state)
    analyze_results(state)

    log("=" * 60)
    log("HYBRID VERIFICATION RUNNER COMPLETED")
    log(f"Total cost: ${state['total_cost']:.4f}")
    log("=" * 60)


if __name__ == "__main__":
    main()

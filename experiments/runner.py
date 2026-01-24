#!/usr/bin/env python3
"""
Autonomous Experiment Runner for LLM Reasoning Verification Tests
Survives crashes/compaction via JSON checkpoint. Tracks costs. Logs progress.

Usage:
    python experiments/runner.py           # Run experiments
    python experiments/runner.py --judge   # Run judge evaluations only
    python experiments/runner.py --analyze # Analyze results only

Monitor progress:
    tail -f experiments/experiment.log
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
STATE_FILE = EXPERIMENTS_DIR / "experiment_state.json"
LOG_FILE = EXPERIMENTS_DIR / "experiment.log"
RESULTS_FILE = EXPERIMENTS_DIR / "experiment_results.json"
BUDGET_LIMIT = 50.0
RETRY_DELAY = 5
MAX_RETRIES = 3

# Pre-registered questions (DO NOT MODIFY after experiment starts)
QUESTIONS = {
    # Factual questions - verifiable, risk of hallucination
    "factual_1": {
        "type": "factual",
        "question": "What were the key technical causes of the Boeing 737 MAX crashes (Lion Air 610 and Ethiopian 302)? Cite specific technical findings from official investigation reports.",
        "notes": "Tests citation accuracy, factual recall, hallucination risk on technical details"
    },
    "factual_2": {
        "type": "factual",
        "question": "What is the actual cost per kilometer of the NYC Second Avenue Subway Phase 1 compared to recent Paris Metro extensions? Provide specific project costs and sources.",
        "notes": "Numeric lookup, hallucination risk, requires precise figures"
    },
    # Reasoning questions - logic-heavy, less verifiable
    "reasoning_1": {
        "type": "reasoning",
        "question": "A bat and ball cost $1.10 together. The bat costs $1.00 more than the ball. How much does the ball cost? Explain your reasoning step by step.",
        "notes": "Classic cognitive bias trap - tests if verification catches intuitive-but-wrong answers"
    },
    "reasoning_2": {
        "type": "reasoning",
        "question": "Should a growing startup with 50 engineers migrate from a monolith to microservices? What are the key factors and tradeoffs? Take a clear position.",
        "notes": "Architecture reasoning, no single right answer, tests logical structure"
    },
}

# Methods to test
METHODS = {
    "baseline": {
        "description": "Single-shot with --rigor flag",
        "calls": 1
    },
    "self_consistency_k5": {
        "description": "Generate 5 samples, synthesize best answer",
        "calls": 2  # 5 samples (1 call with temp diversity) + synthesis
    },
    "self_consistency_k10": {
        "description": "Generate 10 samples, synthesize best answer",
        "calls": 2
    },
    "generic_critique": {
        "description": "Generate -> Generic critique -> Revise",
        "calls": 3
    },
    "cove": {
        "description": "Chain-of-Verification: Draft -> Verification Qs -> Answer them -> Revise",
        "calls": 3
    },
    "reasoning_verification": {
        "description": "Generate -> Check logical steps -> Revise",
        "calls": 3
    },
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
        log(f"Loaded state: {state['total_cost']:.4f} spent, {len([r for r in state['runs'].values() if r.get('generation', {}).get('done')])} generations done")
        return state

    # Initialize state
    state = {
        "total_cost": 0.0,
        "budget_limit": BUDGET_LIMIT,
        "started_at": datetime.now().isoformat(),
        "runs": {}
    }

    # Create run entries for all combinations
    for q_id in QUESTIONS:
        for m_id in METHODS:
            run_id = f"{m_id}__{q_id}"
            state["runs"][run_id] = {
                "question_id": q_id,
                "method_id": m_id,
                "generation": {"done": False, "response": None, "cost": 0.0, "intermediate": []},
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


def parse_cost(output: str) -> float:
    """Extract cost from minds CLI output."""
    # Look for the specific minds CLI cost format at end of output
    # Pattern: "Total: XXXms | Cost: $0.1234 | Models: X/X"
    match = re.search(r'Total:.*\|\s*Cost:\s*\$?([\d.]+)\s*\|', output)
    if match:
        cost = float(match.group(1))
        if cost < 1.0:  # Sanity check - single query shouldn't cost more than $1
            return cost
    return 0.0


def call_minds(prompt: str, model: str = None, rigor: bool = False, timeout: int = 180) -> tuple[str, float]:
    """Call minds CLI and return (response, cost)."""
    cmd = ["minds", "ask"]
    if model:
        cmd.extend(["-m", model])
    if rigor:
        cmd.append("--rigor")
    cmd.append(prompt)

    for attempt in range(MAX_RETRIES):
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )

            full_output = result.stdout + result.stderr
            cost = parse_cost(full_output)

            # Extract response (between the box characters or after synthesis)
            response = result.stdout.strip()

            return response, cost

        except subprocess.TimeoutExpired:
            log(f"Timeout on attempt {attempt + 1}/{MAX_RETRIES}", "WARN")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY * (attempt + 1))
        except Exception as e:
            log(f"Error on attempt {attempt + 1}: {e}", "ERROR")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY * (attempt + 1))

    return "", 0.0


def call_single_model(prompt: str, model: str = "claude", timeout: int = 120) -> tuple[str, float]:
    """Call minds with a single model for faster/cheaper operations."""
    cmd = ["minds", "ask", "--model", model, "--yes", prompt]

    for attempt in range(MAX_RETRIES):
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            full_output = result.stdout + result.stderr
            cost = parse_cost(full_output)
            response = result.stdout.strip()

            if response:
                return response, cost
            else:
                log(f"Empty response on attempt {attempt + 1}, stderr: {result.stderr[:200]}", "WARN")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY)

        except subprocess.TimeoutExpired:
            log(f"Timeout on attempt {attempt + 1}/{MAX_RETRIES}", "WARN")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY * (attempt + 1))
        except Exception as e:
            log(f"Single model call error: {e}", "ERROR")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)

    return "", 0.0


# ============ METHOD IMPLEMENTATIONS ============

def run_baseline(question: str) -> tuple[str, float, list]:
    """Single-shot with --rigor flag."""
    response, cost = call_minds(question, rigor=True)
    return response, cost, []


def run_self_consistency(question: str, k: int) -> tuple[str, float, list]:
    """Generate k samples and synthesize."""
    samples = []
    total_cost = 0.0

    # Generate k samples using single model with temperature variation prompt
    sample_prompt = f"""Answer this question {k} different times, giving each answer your full reasoning.
Number each attempt clearly (Attempt 1, Attempt 2, etc.).
After all attempts, identify which answer appears most often or has the strongest reasoning.

Question: {question}"""

    response, cost = call_single_model(sample_prompt, model="claude", timeout=180)
    samples.append(response)
    total_cost += cost

    # Synthesize
    synthesis_prompt = f"""Here are multiple attempts at answering a question. Identify the answer that appears most consistently or has the strongest reasoning. Give a final synthesized answer.

{response}

Provide your final answer with reasoning."""

    final_response, synth_cost = call_single_model(synthesis_prompt, model="claude")
    total_cost += synth_cost

    return final_response, total_cost, [{"samples": response}]


def run_generic_critique(question: str) -> tuple[str, float, list]:
    """Generate -> Critique -> Revise."""
    intermediates = []
    total_cost = 0.0

    # Step 1: Generate initial response
    response, cost = call_single_model(question, model="claude")
    intermediates.append({"step": "initial", "response": response})
    total_cost += cost

    # Step 2: Critique
    critique_prompt = f"""Critically evaluate this response. Find any errors, unsupported claims, logical gaps, or issues.

Question: {question}

Response to critique:
{response}

Provide a detailed critique."""

    critique, cost = call_single_model(critique_prompt, model="claude")
    intermediates.append({"step": "critique", "response": critique})
    total_cost += cost

    # Step 3: Revise
    revise_prompt = f"""Revise your answer based on this critique.

Original question: {question}

Original response:
{response}

Critique:
{critique}

Provide an improved response that addresses the critique."""

    final_response, cost = call_single_model(revise_prompt, model="claude")
    total_cost += cost

    return final_response, total_cost, intermediates


def run_cove(question: str) -> tuple[str, float, list]:
    """Chain-of-Verification: Draft -> Verification Qs -> Answer them -> Revise."""
    intermediates = []
    total_cost = 0.0

    # Step 1: Draft
    draft, cost = call_single_model(question, model="claude")
    intermediates.append({"step": "draft", "response": draft})
    total_cost += cost

    # Step 2: Generate verification questions
    verify_prompt = f"""Based on this response, generate 5 specific fact-checking questions that would verify the key claims.

Question: {question}

Response to verify:
{draft}

List 5 verification questions, each targeting a specific claim that could be checked."""

    verify_qs, cost = call_single_model(verify_prompt, model="claude")
    intermediates.append({"step": "verification_questions", "response": verify_qs})
    total_cost += cost

    # Step 3: Answer verification questions and revise
    final_prompt = f"""Answer these verification questions about your response, then provide a revised answer that corrects any issues found.

Original question: {question}

Original response:
{draft}

Verification questions:
{verify_qs}

First answer each verification question honestly. Then provide a revised response that addresses any issues."""

    final_response, cost = call_single_model(final_prompt, model="claude")
    total_cost += cost

    return final_response, total_cost, intermediates


def run_reasoning_verification(question: str) -> tuple[str, float, list]:
    """Generate -> Check logical steps -> Revise."""
    intermediates = []
    total_cost = 0.0

    # Step 1: Generate with explicit reasoning
    reason_prompt = f"""Answer this question with explicit step-by-step reasoning. Number each logical step.

{question}"""

    response, cost = call_single_model(reason_prompt, model="claude")
    intermediates.append({"step": "initial", "response": response})
    total_cost += cost

    # Step 2: Verify reasoning steps
    verify_prompt = f"""Check each reasoning step in this response for logical validity.

For each step:
1. Identify the premise and conclusion
2. Check if the conclusion follows from the premise
3. Flag any logical fallacies (false dichotomy, hasty generalization, circular reasoning, etc.)
4. Check if any step depends on an unsupported assumption

Question: {question}

Response to verify:
{response}

Provide your step-by-step verification."""

    verification, cost = call_single_model(verify_prompt, model="claude")
    intermediates.append({"step": "verification", "response": verification})
    total_cost += cost

    # Step 3: Revise based on verification
    revise_prompt = f"""Revise your answer based on the logical verification.

Original question: {question}

Original response:
{response}

Logical verification:
{verification}

Provide a revised response that fixes any logical issues identified."""

    final_response, cost = call_single_model(revise_prompt, model="claude")
    total_cost += cost

    return final_response, total_cost, intermediates


METHOD_RUNNERS = {
    "baseline": run_baseline,
    "self_consistency_k5": lambda q: run_self_consistency(q, 5),
    "self_consistency_k10": lambda q: run_self_consistency(q, 10),
    "generic_critique": run_generic_critique,
    "cove": run_cove,
    "reasoning_verification": run_reasoning_verification,
}


# ============ JUDGE EVALUATION ============

def run_judge(question: str, response: str, question_type: str) -> tuple[dict, float]:
    """Run LLM-as-judge evaluation."""

    judge_prompt = f"""Evaluate this response on two dimensions. Be critical and specific.

Question: {question}

Response to evaluate:
{response}

**Evaluation Criteria:**

1. **Style Score (0-10)**: Depth, specificity, actionability, clarity
   - 0-3: Shallow, vague, not useful
   - 4-6: Adequate but generic
   - 7-8: Good depth and specificity
   - 9-10: Excellent, comprehensive, highly actionable

2. **Adversarial Score (0-10)**: Would this survive fact-checking?
   - 0-3: Contains clear errors or fabrications
   - 4-6: Some claims unverifiable or hedged appropriately
   - 7-8: Most claims defensible, good calibration
   - 9-10: All claims accurate or appropriately caveated

3. **Reasoning Score (0-10)**: Logical structure and validity
   - 0-3: Contains logical fallacies or gaps
   - 4-6: Reasoning is adequate but has weak points
   - 7-8: Sound logical structure
   - 9-10: Rigorous, addresses counterarguments

For each score, provide a brief justification.

Output format:
STYLE_SCORE: [0-10]
STYLE_REASON: [brief reason]
ADVERSARIAL_SCORE: [0-10]
ADVERSARIAL_REASON: [brief reason]
REASONING_SCORE: [0-10]
REASONING_REASON: [brief reason]"""

    result, cost = call_single_model(judge_prompt, model="claude", timeout=120)

    # Parse scores
    scores = {}
    for metric in ["STYLE", "ADVERSARIAL", "REASONING"]:
        match = re.search(rf'{metric}_SCORE:\s*(\d+)', result)
        scores[metric.lower()] = int(match.group(1)) if match else None

        match = re.search(rf'{metric}_REASON:\s*(.+?)(?=\n[A-Z]|$)', result, re.DOTALL)
        scores[f"{metric.lower()}_reason"] = match.group(1).strip() if match else None

    scores["raw_judgment"] = result

    return scores, cost


# ============ MAIN EXECUTION ============

def run_generation_phase(state: dict) -> dict:
    """Run all generations."""
    log("=" * 60)
    log("STARTING GENERATION PHASE")
    log("=" * 60)

    pending = [
        (run_id, run)
        for run_id, run in state["runs"].items()
        if not run["generation"]["done"]
    ]

    log(f"{len(pending)} generations pending, {len(state['runs']) - len(pending)} already done")

    for i, (run_id, run) in enumerate(pending):
        if state["total_cost"] >= state["budget_limit"]:
            log(f"BUDGET LIMIT REACHED: ${state['total_cost']:.4f} >= ${state['budget_limit']}", "WARN")
            break

        q_id = run["question_id"]
        m_id = run["method_id"]
        question = QUESTIONS[q_id]["question"]

        log(f"[{i+1}/{len(pending)}] Running {m_id} on {q_id}...")
        log(f"  Budget: ${state['total_cost']:.4f} / ${state['budget_limit']:.2f}")

        start_time = time.time()

        try:
            runner = METHOD_RUNNERS[m_id]
            response, cost, intermediates = runner(question)

            elapsed = time.time() - start_time

            run["generation"] = {
                "done": True,
                "response": response,
                "cost": cost,
                "intermediate": intermediates,
                "elapsed_seconds": elapsed
            }

            state["total_cost"] += cost
            save_state(state)

            log(f"  ✓ Done in {elapsed:.1f}s, cost: ${cost:.4f}")

        except Exception as e:
            log(f"  ✗ ERROR: {e}", "ERROR")
            run["generation"]["error"] = str(e)
            save_state(state)

        # Rate limit protection
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
        response = run["generation"]["response"]

        log(f"[{i+1}/{len(pending)}] Judging {run_id}...")

        try:
            scores, cost = run_judge(question, response, question_type)

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
            log(f"  ✓ Style: {style}/10, Adversarial: {adv}/10, Reasoning: {reason}/10, cost: ${cost:.4f}")

        except Exception as e:
            log(f"  ✗ ERROR: {e}", "ERROR")
            run["judge"]["error"] = str(e)
            save_state(state)

        time.sleep(1)

    return state


def analyze_results(state: dict):
    """Analyze and summarize results with full methodology audit."""
    log("=" * 60)
    log("ANALYZING RESULTS")
    log("=" * 60)

    results = {
        "summary": {},
        "by_method": {},
        "by_question_type": {},
        "by_question": {},
        "methodology_audit": {},
        "consistency": {},
        "total_cost": state["total_cost"]
    }

    # Collect scores
    for run_id, run in state["runs"].items():
        if not run["judge"]["done"]:
            continue

        m_id = run["method_id"]
        q_id = run["question_id"]
        q_type = QUESTIONS[q_id]["type"]
        scores = run["judge"]["scores"]

        # By method
        if m_id not in results["by_method"]:
            results["by_method"][m_id] = {"style": [], "adversarial": [], "reasoning": []}
        for metric in ["style", "adversarial", "reasoning"]:
            if scores.get(metric) is not None:
                results["by_method"][m_id][metric].append(scores[metric])

        # By question type
        if q_type not in results["by_question_type"]:
            results["by_question_type"][q_type] = {"style": [], "adversarial": [], "reasoning": []}
        for metric in ["style", "adversarial", "reasoning"]:
            if scores.get(metric) is not None:
                results["by_question_type"][q_type][metric].append(scores[metric])

        # By question
        if q_id not in results["by_question"]:
            results["by_question"][q_id] = {}
        results["by_question"][q_id][m_id] = scores

    # ============ METHODOLOGY AUDIT ============
    log("\n=== METHODOLOGY AUDIT ===")

    n_questions = len(QUESTIONS)
    n_methods = len(METHODS)

    # Check sample size
    if n_questions < 10:
        log(f"⚠ WARNING: N={n_questions} is too small for reliable conclusions (pilot only)")
        results["methodology_audit"]["sample_size"] = "insufficient"
    elif n_questions < 30:
        log(f"⚠ CAUTION: N={n_questions} is exploratory (need N>30 for confirmatory)")
        results["methodology_audit"]["sample_size"] = "exploratory"
    else:
        log(f"✓ N={n_questions} is adequate for confirmatory analysis")
        results["methodology_audit"]["sample_size"] = "adequate"

    # Check for ceiling effects
    all_scores = []
    for m_data in results["by_method"].values():
        all_scores.extend(m_data.get("style", []))
        all_scores.extend(m_data.get("adversarial", []))
        all_scores.extend(m_data.get("reasoning", []))

    if all_scores:
        avg_score = sum(all_scores) / len(all_scores)
        min_score = min(all_scores)
        max_score = max(all_scores)
        if min_score >= 7:
            log(f"⚠ WARNING: Ceiling effect detected (min={min_score}, avg={avg_score:.1f})")
            log("  Questions may be too easy - consider harder questions")
            results["methodology_audit"]["ceiling_effect"] = True
        else:
            results["methodology_audit"]["ceiling_effect"] = False

    # ============ COMPUTE AVERAGES WITH VARIANCE ============
    log("\n=== RESULTS BY METHOD (with variance) ===")
    log(f"{'Method':<25} | {'Style':^12} | {'Adversarial':^12} | {'Reasoning':^12} | Combined")
    log("-" * 80)

    for m_id, metrics in results["by_method"].items():
        for metric in ["style", "adversarial", "reasoning"]:
            scores = metrics[metric]
            if scores:
                avg = sum(scores) / len(scores)
                variance = max(scores) - min(scores) if len(scores) > 1 else 0
                metrics[f"avg_{metric}"] = avg
                metrics[f"range_{metric}"] = variance
            else:
                metrics[f"avg_{metric}"] = 0
                metrics[f"range_{metric}"] = 0

        avg_s = metrics["avg_style"]
        avg_a = metrics["avg_adversarial"]
        avg_r = metrics["avg_reasoning"]
        combined = (avg_s + avg_a + avg_r) / 3
        metrics["combined"] = combined

        range_s = metrics["range_style"]
        range_a = metrics["range_adversarial"]
        range_r = metrics["range_reasoning"]

        log(f"{m_id:<25} | {avg_s:.1f} (±{range_s}) | {avg_a:.1f} (±{range_a}) | {avg_r:.1f} (±{range_r}) | {combined:.2f}")

    # ============ CONSISTENCY ANALYSIS ============
    log("\n=== CONSISTENCY ANALYSIS ===")

    for m_id, metrics in results["by_method"].items():
        range_a = metrics.get("range_adversarial", 0)
        if range_a >= 4:
            log(f"⚠ {m_id}: HIGH variance (range={range_a}) - unreliable")
            results["consistency"][m_id] = "high_variance"
        elif range_a >= 2:
            log(f"○ {m_id}: Moderate variance (range={range_a})")
            results["consistency"][m_id] = "moderate_variance"
        else:
            log(f"✓ {m_id}: Low variance (range={range_a}) - consistent")
            results["consistency"][m_id] = "consistent"

    # ============ BY QUESTION TYPE ============
    log("\n=== RESULTS BY QUESTION TYPE ===")
    for q_type, metrics in results["by_question_type"].items():
        avg_style = sum(metrics["style"]) / len(metrics["style"]) if metrics["style"] else 0
        avg_adv = sum(metrics["adversarial"]) / len(metrics["adversarial"]) if metrics["adversarial"] else 0
        avg_reason = sum(metrics["reasoning"]) / len(metrics["reasoning"]) if metrics["reasoning"] else 0
        log(f"{q_type:15s} | Style: {avg_style:.1f} | Adversarial: {avg_adv:.1f} | Reasoning: {avg_reason:.1f}")

    # ============ CONCLUSIONS BY CONFIDENCE ============
    log("\n=== CONCLUSIONS BY CONFIDENCE ===")

    if n_questions < 10:
        log("STRONG: None (insufficient N)")
        log("MODERATE: None (insufficient N)")
        log("EXPLORATORY: All findings are pilot-level only")
    else:
        log("Note: Confidence levels require manual review - see analysis_checklist.md")

    log(f"\n=== TOTAL COST: ${state['total_cost']:.4f} ===")

    # Save results
    with open(RESULTS_FILE, "w") as f:
        json.dump(results, f, indent=2)

    log(f"Results saved to {RESULTS_FILE}")

    return results


def main():
    """Main entry point."""
    log("=" * 60)
    log("EXPERIMENT RUNNER STARTED")
    log(f"State file: {STATE_FILE}")
    log(f"Log file: {LOG_FILE}")
    log(f"Budget limit: ${BUDGET_LIMIT}")
    log("=" * 60)

    # Parse args
    judge_only = "--judge" in sys.argv
    analyze_only = "--analyze" in sys.argv

    state = load_state()

    if analyze_only:
        analyze_results(state)
        return

    if not judge_only:
        state = run_generation_phase(state)

    state = run_judge_phase(state)

    # Analyze
    analyze_results(state)

    log("=" * 60)
    log("EXPERIMENT RUNNER COMPLETED")
    log(f"Total cost: ${state['total_cost']:.4f}")
    log("=" * 60)


if __name__ == "__main__":
    main()

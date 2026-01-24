#!/usr/bin/env python3
"""
Experiment Runner v2 - Improved methodology based on pilot learnings.

Key improvements:
- GPT-5.2 as base model for fair comparison
- minds --rigor as reference point
- Harder questions (stratified by type)
- Track tokens per method
- Multiple seeds per question for variance
- Separated contested questions from accuracy metrics

Usage:
    python3 experiments/runner_v2.py           # Run experiments
    python3 experiments/runner_v2.py --analyze # Analyze only
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
STATE_FILE = EXPERIMENTS_DIR / "experiment_state_v2.json"
LOG_FILE = EXPERIMENTS_DIR / "experiment_v2.log"
RESULTS_FILE = EXPERIMENTS_DIR / "experiment_results_v2.json"
BUDGET_LIMIT = 50.0
RETRY_DELAY = 5
MAX_RETRIES = 3
SEEDS_PER_QUESTION = 2  # Run each method-question pair twice for variance

# Pre-registered questions - HARDER than pilot
QUESTIONS = {
    # === FACTUAL-HARD (hallucination traps, <70% baseline expected) ===
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
        "notes": "Stockholm Convention is 2001, not 1987 (Montreal Protocol is 1987) - tests temporal accuracy",
        "ground_truth": "Should note Stockholm Convention is 2001, not 1987"
    },
    "factual_hard_4": {
        "type": "factual",
        "question": "What was the exact cost per mile of California High-Speed Rail Phase 1 construction as of 2023, and how does it compare to Japan's Shinkansen extensions?",
        "notes": "Precise figures often fabricated - tests numeric accuracy",
        "ground_truth": "Should acknowledge figures are estimates/contested"
    },

    # === REASONING-HARD (logic puzzles, not memorized) ===
    "reasoning_hard_1": {
        "type": "reasoning",
        "question": "A bat and ball cost $1.10 together. The bat costs $1.00 more than the ball. How much does the ball cost? Show your work step by step.",
        "notes": "Classic cognitive bias trap - answer is $0.05, not $0.10",
        "ground_truth": "$0.05"
    },
    "reasoning_hard_2": {
        "type": "reasoning",
        "question": "You have 12 coins, one of which is counterfeit (either heavier or lighter than the rest). Using a balance scale exactly 3 times, how would you identify the counterfeit coin AND determine whether it's heavier or lighter?",
        "notes": "Complex constraint satisfaction - requires systematic approach",
        "ground_truth": "Valid algorithm that works in all cases"
    },
    "reasoning_hard_3": {
        "type": "reasoning",
        "question": "Three people check into a hotel room that costs $30. They each pay $10. Later, the clerk realizes the room was only $25 and gives $5 to the bellhop to return. The bellhop keeps $2 and gives $1 back to each person. Now each person paid $9 (total $27), plus the bellhop has $2, equals $29. Where's the missing dollar?",
        "notes": "Classic misdirection puzzle - tests logical analysis",
        "ground_truth": "The framing is wrong - $27 includes the $2, shouldn't add them"
    },
    "reasoning_hard_4": {
        "type": "reasoning",
        "question": "A snail is at the bottom of a 30-foot well. Each day it climbs up 3 feet, but each night it slides back down 2 feet. On which day does the snail reach the top of the well?",
        "notes": "Edge case reasoning - answer is day 28, not day 30",
        "ground_truth": "Day 28 (reaches top during day, doesn't slide back)"
    },

    # === CONTESTED/ARCHITECTURAL (no single right answer, tests reasoning quality) ===
    "contested_1": {
        "type": "contested",
        "question": "Should a 50-person engineering team at a growth-stage startup migrate from a Django monolith to microservices? They're experiencing scaling issues but have limited DevOps expertise. Take a clear position with reasoning.",
        "notes": "Architectural decision - tests reasoning structure, not correctness",
        "ground_truth": None  # No single right answer
    },
    "contested_2": {
        "type": "contested",
        "question": "Is remote work better for company culture long-term compared to in-office work? Consider a 200-person tech company. Take a position and defend it.",
        "notes": "Contested topic - tests argument quality",
        "ground_truth": None
    },
    "contested_3": {
        "type": "contested",
        "question": "Should AI companies be required to open-source their large language models for safety research? Argue one side with specific reasoning.",
        "notes": "Policy question - tests logical structure",
        "ground_truth": None
    },
    "contested_4": {
        "type": "contested",
        "question": "What explains the productivity paradox - why hasn't AI visibly boosted economic productivity statistics despite widespread adoption? Provide a clear thesis with supporting arguments.",
        "notes": "Analytical question - tests reasoning depth",
        "ground_truth": None
    },
}

# Methods to test - all use GPT except minds_rigor
METHODS = {
    "gpt_baseline": {
        "description": "GPT-5.2 single-shot, no verification",
        "model": "gpt",
        "calls": 1,
        "type": "baseline"
    },
    "minds_rigor": {
        "description": "5-model minds --rigor (production reference)",
        "model": "multi",
        "calls": 1,
        "type": "reference"
    },
    "generic_critique": {
        "description": "Generate → Critique → Revise (GPT-5.2)",
        "model": "gpt",
        "calls": 3,
        "type": "verification"
    },
    "cove": {
        "description": "Chain-of-Verification (GPT-5.2)",
        "model": "gpt",
        "calls": 3,
        "type": "verification"
    },
    "reasoning_verification": {
        "description": "Explicit logic checking (GPT-5.2)",
        "model": "gpt",
        "calls": 3,
        "type": "verification"
    },
    "temperature_diversity": {
        "description": "GPT at temp 0.0, 0.7, 1.0 → synthesize",
        "model": "gpt",
        "calls": 4,
        "type": "ensemble"
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
        done = sum(1 for r in state['runs'].values() if r.get('generation', {}).get('done'))
        log(f"Loaded state: ${state['total_cost']:.4f} spent, {done} generations done")
        return state

    # Initialize state
    state = {
        "total_cost": 0.0,
        "total_tokens": 0,
        "budget_limit": BUDGET_LIMIT,
        "started_at": datetime.now().isoformat(),
        "runs": {}
    }

    # Create run entries for all combinations (with seeds)
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
    log(f"Initialized state with {len(state['runs'])} runs ({len(QUESTIONS)} questions × {len(METHODS)} methods × {SEEDS_PER_QUESTION} seeds)")
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

    # Cost pattern: "Total: XXXms | Cost: $0.1234 | Models: X/X"
    match = re.search(r'Total:.*\|\s*Cost:\s*\$?([\d.]+)\s*\|', output)
    if match:
        cost = float(match.group(1))
        if cost > 1.0:  # Sanity check
            cost = 0.0

    # Estimate tokens from response length (rough: 4 chars per token)
    tokens = len(output) // 4

    return cost, tokens


def call_minds_rigor(prompt: str, timeout: int = 180) -> tuple[str, float, int]:
    """Call minds with --rigor flag (5 models)."""
    cmd = ["minds", "ask", "--rigor", "--yes", prompt]

    for attempt in range(MAX_RETRIES):
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            full_output = result.stdout + result.stderr
            cost, tokens = parse_cost_and_tokens(full_output)
            return result.stdout.strip(), cost, tokens
        except subprocess.TimeoutExpired:
            log(f"Timeout on attempt {attempt + 1}/{MAX_RETRIES}", "WARN")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY * (attempt + 1))
        except Exception as e:
            log(f"Error: {e}", "ERROR")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)

    return "", 0.0, 0


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


# ============ METHOD IMPLEMENTATIONS ============

def run_gpt_baseline(question: str) -> tuple[str, float, int, list]:
    """GPT-5.2 single-shot baseline."""
    response, cost, tokens = call_single_model(question, model="gpt")
    return response, cost, tokens, []


def run_minds_rigor(question: str) -> tuple[str, float, int, list]:
    """minds --rigor (5-model reference)."""
    response, cost, tokens = call_minds_rigor(question)
    return response, cost, tokens, []


def run_generic_critique(question: str) -> tuple[str, float, int, list]:
    """Generate → Critique → Revise."""
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


def run_cove(question: str) -> tuple[str, float, int, list]:
    """Chain-of-Verification."""
    intermediates = []
    total_cost, total_tokens = 0.0, 0

    # Step 1: Draft
    draft, cost, tokens = call_single_model(question, model="gpt")
    intermediates.append({"step": "draft", "response": draft[:500]})
    total_cost += cost
    total_tokens += tokens

    # Step 2: Generate verification questions
    verify_prompt = f"""Based on this response, generate 5 specific fact-checking questions that would verify the key claims.

Question: {question}

Response to verify:
{draft}

List 5 verification questions, each targeting a specific claim that could be checked."""

    verify_qs, cost, tokens = call_single_model(verify_prompt, model="gpt")
    intermediates.append({"step": "verification_questions", "response": verify_qs[:500]})
    total_cost += cost
    total_tokens += tokens

    # Step 3: Answer verification questions and revise
    final_prompt = f"""Answer these verification questions about your response, then provide a revised answer that corrects any issues found.

Original question: {question}

Original response:
{draft}

Verification questions:
{verify_qs}

First answer each verification question honestly. Then provide a revised response that addresses any issues."""

    final_response, cost, tokens = call_single_model(final_prompt, model="gpt")
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
3. Flag any logical fallacies (false dichotomy, hasty generalization, circular reasoning, etc.)
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


def run_temperature_diversity(question: str) -> tuple[str, float, int, list]:
    """Generate at different temperatures, then synthesize."""
    intermediates = []
    total_cost, total_tokens = 0.0, 0
    responses = []

    # Note: minds CLI doesn't support temperature directly, so we simulate with prompts
    prompts = [
        f"Answer this question precisely and deterministically:\n\n{question}",
        f"Answer this question with balanced analysis:\n\n{question}",
        f"Answer this question creatively, exploring unconventional angles:\n\n{question}",
    ]

    for i, prompt in enumerate(prompts):
        resp, cost, tokens = call_single_model(prompt, model="gpt")
        responses.append(resp)
        intermediates.append({"step": f"temp_{i}", "response": resp[:500]})
        total_cost += cost
        total_tokens += tokens

    # Synthesize (deterministic)
    synth_prompt = f"""You are given three different responses to the same question. Synthesize the best answer by:
1. Identifying points of agreement
2. Resolving contradictions with the most well-reasoned position
3. Preserving unique insights from each

Question: {question}

Response A:
{responses[0]}

Response B:
{responses[1]}

Response C:
{responses[2]}

Provide a synthesized final answer."""

    final_response, cost, tokens = call_single_model(synth_prompt, model="gpt")
    total_cost += cost
    total_tokens += tokens

    return final_response, total_cost, total_tokens, intermediates


METHOD_RUNNERS = {
    "gpt_baseline": run_gpt_baseline,
    "minds_rigor": run_minds_rigor,
    "generic_critique": run_generic_critique,
    "cove": run_cove,
    "reasoning_verification": run_reasoning_verification,
    "temperature_diversity": run_temperature_diversity,
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

4. **Verification Breakdown (yes/no)**: Did the response get WORSE than a simple direct answer would? (fabricate things, add errors, overcomplicate)

Output format:
STYLE_SCORE: [0-10]
ADVERSARIAL_SCORE: [0-10]
REASONING_SCORE: [0-10]
VERIFICATION_BREAKDOWN: [yes/no]
BRIEF_JUSTIFICATION: [2-3 sentences]"""

    result, cost, _ = call_single_model(judge_prompt, model="gpt", timeout=120)

    # Parse scores
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
        seed = run["seed"]
        question = QUESTIONS[q_id]["question"]

        log(f"[{i+1}/{len(pending)}] Running {m_id} on {q_id} (seed {seed})...")
        log(f"  Budget: ${state['total_cost']:.4f} / ${state['budget_limit']:.2f}")

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

            log(f"  ✓ Done in {elapsed:.1f}s, cost: ${cost:.4f}, ~{tokens} tokens")

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
            breakdown = "⚠BREAKDOWN" if scores.get("verification_breakdown") else ""
            log(f"  ✓ S:{style} A:{adv} R:{reason} {breakdown}")

        except Exception as e:
            log(f"  ✗ ERROR: {e}", "ERROR")
            run["judge"]["error"] = str(e)
            save_state(state)

        time.sleep(1)

    return state


def analyze_results(state: dict):
    """Analyze results with full methodology audit."""
    log("=" * 60)
    log("ANALYZING RESULTS (v2)")
    log("=" * 60)

    results = {
        "by_method": {},
        "by_question_type": {},
        "by_question": {},
        "methodology_audit": {},
        "verification_breakdowns": [],
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

        # Track verification breakdowns
        if scores.get("verification_breakdown"):
            results["verification_breakdowns"].append({
                "run_id": run_id,
                "method": m_id,
                "question": q_id,
                "justification": scores.get("justification", "")
            })

        # By method
        if m_id not in results["by_method"]:
            results["by_method"][m_id] = {
                "style": [], "adversarial": [], "reasoning": [],
                "tokens": [], "costs": [], "breakdowns": 0
            }

        for metric in ["style", "adversarial", "reasoning"]:
            if scores.get(metric) is not None:
                results["by_method"][m_id][metric].append(scores[metric])

        results["by_method"][m_id]["tokens"].append(gen.get("tokens", 0))
        results["by_method"][m_id]["costs"].append(gen.get("cost", 0))
        if scores.get("verification_breakdown"):
            results["by_method"][m_id]["breakdowns"] += 1

        # By question type (separate contested from accuracy)
        if q_type not in results["by_question_type"]:
            results["by_question_type"][q_type] = {"style": [], "adversarial": [], "reasoning": []}
        for metric in ["style", "adversarial", "reasoning"]:
            if scores.get(metric) is not None:
                results["by_question_type"][q_type][metric].append(scores[metric])

    # ============ METHODOLOGY AUDIT ============
    log("\n=== METHODOLOGY AUDIT ===")

    n_questions = len(QUESTIONS)
    n_methods = len(METHODS)
    total_runs = n_questions * n_methods * SEEDS_PER_QUESTION

    log(f"Design: {n_questions} questions × {n_methods} methods × {SEEDS_PER_QUESTION} seeds = {total_runs} runs")

    if n_questions < 10:
        log(f"⚠ WARNING: N={n_questions} is exploratory only")
        results["methodology_audit"]["sample_size"] = "exploratory"
    else:
        log(f"✓ N={n_questions} adequate for exploration")
        results["methodology_audit"]["sample_size"] = "adequate"

    # ============ RESULTS BY METHOD ============
    log("\n=== RESULTS BY METHOD (with tokens) ===")
    log(f"{'Method':<22} | {'Style':^7} | {'Adv':^7} | {'Reason':^7} | {'Tokens':^8} | {'Breakdowns':^10}")
    log("-" * 85)

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

        log(f"{m_id:<22} | {avg_s:>5.1f}  | {avg_a:>5.1f}  | {avg_r:>5.1f}  | {avg_tokens:>7.0f} | {breakdowns}/{n}")

    # ============ BY QUESTION TYPE ============
    log("\n=== RESULTS BY QUESTION TYPE ===")
    log("(Note: 'contested' measures reasoning quality, not accuracy)")

    for q_type, data in results["by_question_type"].items():
        avg_s = sum(data["style"])/len(data["style"]) if data["style"] else 0
        avg_a = sum(data["adversarial"])/len(data["adversarial"]) if data["adversarial"] else 0
        avg_r = sum(data["reasoning"])/len(data["reasoning"]) if data["reasoning"] else 0
        log(f"{q_type:<12} | Style: {avg_s:.1f} | Adversarial: {avg_a:.1f} | Reasoning: {avg_r:.1f}")

    # ============ VERIFICATION BREAKDOWNS ============
    if results["verification_breakdowns"]:
        log(f"\n=== VERIFICATION BREAKDOWNS ({len(results['verification_breakdowns'])} cases) ===")
        for bd in results["verification_breakdowns"][:5]:
            log(f"  {bd['method']} on {bd['question']}: {bd['justification'][:100]}...")

    # ============ SUMMARY ============
    log(f"\n=== SUMMARY ===")
    log(f"Total cost: ${state['total_cost']:.4f}")
    log(f"Total tokens: ~{state.get('total_tokens', 0):,}")
    log(f"Verification breakdowns: {len(results['verification_breakdowns'])}/{total_runs}")

    # Save results
    with open(RESULTS_FILE, "w") as f:
        json.dump(results, f, indent=2)

    log(f"Results saved to {RESULTS_FILE}")

    return results


def main():
    """Main entry point."""
    log("=" * 60)
    log("EXPERIMENT RUNNER v2 STARTED")
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
    log("EXPERIMENT RUNNER v2 COMPLETED")
    log(f"Total cost: ${state['total_cost']:.4f}")
    log("=" * 60)


if __name__ == "__main__":
    main()

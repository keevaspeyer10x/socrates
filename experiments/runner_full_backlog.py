#!/usr/bin/env python3
"""
Full Experiment Backlog Runner - Runs all experiments from next_experiments.md

Experiments:
- 12A: Self-Consistency Sampling (k=5 samples, majority vote)
- 8B: Anti-Fabrication Prompt
- 5A: Self-Critique on Multiple Question Types
- 12B: Chain-of-Verification (CoVe) - structured fact-checking
- 6A: Prompt Engineering Combinations
- 10B: Structural Element Isolation
- Additive Verification (critique + reasoning stacked)

Usage:
    python3 experiments/runner_full_backlog.py           # Run all experiments
    python3 experiments/runner_full_backlog.py --analyze # Analyze only
"""

import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from collections import Counter

# Configuration
EXPERIMENTS_DIR = Path(__file__).parent
STATE_FILE = EXPERIMENTS_DIR / "experiment_state_backlog.json"
LOG_FILE = EXPERIMENTS_DIR / "experiment_backlog.log"
RESULTS_FILE = EXPERIMENTS_DIR / "experiment_results_backlog.json"
BUDGET_LIMIT = 100.0
RETRY_DELAY = 5
MAX_RETRIES = 3

# ============ TEST QUESTIONS ============

# Questions for different experiment types
QUESTIONS = {
    # Factual (hallucination traps)
    "factual_1": {
        "type": "factual",
        "question": "What were the key technical causes of the 737 MAX crashes?",
        "notes": "Factual/verifiable question",
    },
    "factual_2": {
        "type": "factual",
        "question": "What percentage of Fortune 500 CEOs have Harvard MBAs specifically? Cite your source.",
        "notes": "Commonly fabricated statistic",
    },

    # Reasoning
    "reasoning_1": {
        "type": "reasoning",
        "question": "A bat and ball cost $1.10 together. The bat costs $1.00 more than the ball. How much does the ball cost? Show your work.",
        "ground_truth": "$0.05",
    },
    "reasoning_2": {
        "type": "reasoning",
        "question": "What explains the productivity paradox - why hasn't AI visibly boosted economic productivity statistics despite widespread adoption?",
        "notes": "Causal reasoning question",
    },

    # Contested/architectural
    "contested_1": {
        "type": "contested",
        "question": "Should a 50-person engineering team at a growth-stage startup migrate from a Django monolith to microservices? They're experiencing scaling issues but have limited DevOps expertise.",
    },
    "contested_2": {
        "type": "contested",
        "question": "Is remote work better for company culture long-term compared to in-office work? Consider a 200-person tech company.",
    },

    # Prediction
    "prediction_1": {
        "type": "prediction",
        "question": "What will be the dominant AI model architecture in 2028?",
    },
}

# ============ EXPERIMENT DEFINITIONS ============

EXPERIMENTS = {
    # Experiment 12A: Self-Consistency Sampling
    "12A_self_consistency": {
        "name": "Self-Consistency Sampling",
        "description": "Generate k=5 samples and use majority voting",
        "questions": ["factual_1", "reasoning_1", "contested_1"],
    },

    # Experiment 8B: Anti-Fabrication Prompt
    "8B_anti_fabrication": {
        "name": "Anti-Fabrication Prompt",
        "description": "Test explicit anti-fabrication instruction",
        "questions": ["factual_1", "factual_2"],
    },

    # Experiment 5A: Self-Critique on Multiple Question Types
    "5A_self_critique_types": {
        "name": "Self-Critique on Multiple Question Types",
        "description": "Test if self-critique generalizes across question types",
        "questions": ["factual_1", "reasoning_2", "prediction_1", "contested_2"],
    },

    # Experiment 12B: Chain-of-Verification
    "12B_cove": {
        "name": "Chain-of-Verification (Structured)",
        "description": "Generate specific fact-checking questions instead of generic critique",
        "questions": ["factual_1", "factual_2", "reasoning_1"],
    },

    # Experiment 6A: Prompt Engineering Combinations
    "6A_prompt_combos": {
        "name": "Prompt Engineering Combinations",
        "description": "Test if prompt improvements stack",
        "questions": ["factual_1", "contested_1"],
    },

    # Experiment 10B: Structural Element Isolation
    "10B_structural_elements": {
        "name": "Structural Element Isolation",
        "description": "Which structural thinking element provides most lift?",
        "questions": ["contested_1", "reasoning_2"],
    },

    # Additive Verification (from hybrid experiment learnings)
    "additive_verification": {
        "name": "Additive Verification",
        "description": "Always critique + conditional specialized verification (stacked)",
        "questions": ["factual_1", "reasoning_1", "contested_1"],
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
    """Load or initialize state."""
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            state = json.load(f)
        log(f"Loaded state: ${state.get('total_cost', 0):.4f} spent")
        return state

    return {
        "total_cost": 0.0,
        "started_at": datetime.now().isoformat(),
        "experiments": {},
        "runs": {}
    }


def save_state(state: dict):
    """Atomic save."""
    state["last_updated"] = datetime.now().isoformat()
    tmp_file = STATE_FILE.with_suffix(".tmp")
    with open(tmp_file, "w") as f:
        json.dump(state, f, indent=2)
    os.replace(tmp_file, STATE_FILE)


def call_minds(prompt: str, args: list = None, timeout: int = 180) -> tuple[str, float]:
    """Call minds CLI with arguments."""
    cmd = ["minds", "ask"] + (args or []) + ["--yes", prompt]

    for attempt in range(MAX_RETRIES):
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            output = result.stdout.strip()

            # Parse cost
            cost = 0.0
            match = re.search(r'Cost:\s*\$?([\d.]+)', result.stdout + result.stderr)
            if match:
                cost = float(match.group(1))
                if cost > 1.0:
                    cost = 0.0

            if output:
                return output, cost
            else:
                log(f"Empty response, retrying ({attempt + 1}/{MAX_RETRIES})", "WARN")
                time.sleep(RETRY_DELAY)

        except subprocess.TimeoutExpired:
            log(f"Timeout ({attempt + 1}/{MAX_RETRIES})", "WARN")
            time.sleep(RETRY_DELAY * 2)
        except Exception as e:
            log(f"Error: {e}", "ERROR")
            time.sleep(RETRY_DELAY)

    return "", 0.0


def call_single_model(prompt: str, model: str = "gpt", timeout: int = 120) -> tuple[str, float]:
    """Call single model."""
    return call_minds(prompt, ["--model", model], timeout)


# ============ METHOD IMPLEMENTATIONS ============

def run_baseline(question: str) -> tuple[str, float, dict]:
    """GPT baseline single-shot."""
    response, cost = call_single_model(question)
    return response, cost, {"method": "baseline"}


def run_rigor(question: str) -> tuple[str, float, dict]:
    """minds --rigor (5-model synthesis)."""
    response, cost = call_minds(question, ["--rigor"])
    return response, cost, {"method": "rigor"}


def run_self_critique(question: str) -> tuple[str, float, dict]:
    """Generate → Critique → Revise."""
    total_cost = 0.0
    intermediates = {}

    # Step 1: Generate
    response, cost = call_single_model(question)
    total_cost += cost
    intermediates["initial"] = response[:500]

    # Step 2: Critique
    critique_prompt = f"""Critically evaluate this response for:
- Factual accuracy (any claims that can't be verified?)
- Logical reasoning (any gaps or fallacies?)
- Completeness (anything important missing?)

Question: {question}

Response:
{response}

Provide specific critique."""

    critique, cost = call_single_model(critique_prompt)
    total_cost += cost
    intermediates["critique"] = critique[:500]

    # Step 3: Revise
    revise_prompt = f"""Revise this response to address the critique.

Original question: {question}

Original response:
{response}

Critique:
{critique}

Provide an improved response."""

    final, cost = call_single_model(revise_prompt)
    total_cost += cost

    return final, total_cost, {"method": "self_critique", "intermediates": intermediates}


def run_self_consistency_k5(question: str) -> tuple[str, float, dict]:
    """Experiment 12A: Generate k=5 samples and majority vote."""
    total_cost = 0.0
    samples = []

    # Generate 5 independent samples
    for i in range(5):
        response, cost = call_single_model(question)
        samples.append(response)
        total_cost += cost
        time.sleep(1)  # Rate limit

    # Synthesize with majority voting instruction
    synth_prompt = f"""You have 5 independent responses to the same question. Analyze them and provide the best answer using these rules:

1. Where responses AGREE, that's likely correct - use it
2. Where responses DISAGREE, pick the most well-reasoned position
3. If a claim appears in 3+ responses, treat it as reliable
4. If a claim only appears in 1 response, scrutinize it carefully

Question: {question}

Response 1:
{samples[0][:1500]}

Response 2:
{samples[1][:1500]}

Response 3:
{samples[2][:1500]}

Response 4:
{samples[3][:1500]}

Response 5:
{samples[4][:1500]}

Synthesize the best answer using majority voting principles."""

    final, cost = call_single_model(synth_prompt, timeout=180)
    total_cost += cost

    return final, total_cost, {"method": "self_consistency_k5", "n_samples": 5}


def run_anti_fabrication(question: str) -> tuple[str, float, dict]:
    """Experiment 8B: Explicit anti-fabrication instruction."""
    enhanced_prompt = f"""Answer this question carefully.

IMPORTANT: Do not fabricate statistics, numbers, or citations. If you don't have a verified source for a specific figure, say "I don't have a verified source for a specific figure" rather than inventing one. Be precise about what you know vs what you're estimating.

Question: {question}"""

    response, cost = call_single_model(enhanced_prompt)
    return response, cost, {"method": "anti_fabrication"}


def run_cove_structured(question: str) -> tuple[str, float, dict]:
    """Experiment 12B: Chain-of-Verification with structured fact-checking."""
    total_cost = 0.0
    intermediates = {}

    # Step 1: Draft
    draft, cost = call_single_model(question)
    total_cost += cost
    intermediates["draft"] = draft[:500]

    # Step 2: Generate SPECIFIC verification questions
    verify_prompt = f"""Generate 5 specific fact-checking questions for this response. Each question should:
- Target ONE specific claim
- Be answerable with a fact-check
- Not be vague or general

Response to verify:
{draft}

Format: List 5 specific verification questions."""

    questions, cost = call_single_model(verify_prompt)
    total_cost += cost
    intermediates["verify_questions"] = questions[:500]

    # Step 3: Answer verification questions independently, then revise
    final_prompt = f"""First, answer these verification questions honestly. Then revise the original response.

Original question: {question}

Original draft:
{draft}

Verification questions:
{questions}

1. Answer each verification question
2. Note any claims that fail verification
3. Provide a revised response that fixes issues"""

    final, cost = call_single_model(final_prompt, timeout=180)
    total_cost += cost

    return final, total_cost, {"method": "cove_structured", "intermediates": intermediates}


def run_prompt_combo(question: str, variant: str) -> tuple[str, float, dict]:
    """Experiment 6A: Different prompt combinations."""

    prompts = {
        "baseline": question,
        "truth_aware": f"""Claims in your response will be adversarially challenged. Avoid absolute language. Be precise.

{question}""",
        "citation": f"""Cite sources for factual claims where you can. If you can't cite a source, acknowledge it.

{question}""",
        "thoroughness": f"""Short answers score poorly. Be thorough and comprehensive.

{question}""",
        "confidence": f"""Mark each major claim with confidence: HIGH (verified), MEDIUM (likely), or LOW (uncertain).

{question}""",
        "combined": f"""Claims will be adversarially challenged - avoid absolute language.
Cite sources where possible; acknowledge when you can't.
Be thorough - short answers score poorly.
Mark claims as HIGH/MEDIUM/LOW confidence.

{question}"""
    }

    prompt = prompts.get(variant, question)
    response, cost = call_single_model(prompt)
    return response, cost, {"method": f"prompt_{variant}"}


def run_structural_element(question: str, element: str) -> tuple[str, float, dict]:
    """Experiment 10B: Test individual structural elements."""

    element_prompts = {
        "disaggregation": f"""First, break this question into 3-5 sub-questions. Then answer each sub-question before synthesizing a final answer.

{question}""",
        "five_whys": f"""Trace this to root causes using the 5 Whys technique. For the core issue, ask "why" 5 times to reach the fundamental cause. Then answer based on that analysis.

{question}""",
        "known_vs_contested": f"""Separate your answer into two clear sections:
1. WHAT WE KNOW (high-confidence, well-established facts)
2. WHAT'S CONTESTED (areas of genuine disagreement or uncertainty)

{question}""",
        "eighty_twenty": f"""Identify the ONE factor that explains 80% of this issue. Focus your answer on that core driver rather than exhaustively listing all factors.

{question}""",
        "steelman": f"""Before answering, present the STRONGEST argument against your likely conclusion. Then respond to that argument in your answer.

{question}""",
        "what_wont_work": f"""Before making recommendations, explicitly list 2-3 approaches that WON'T work and why. Then provide your actual recommendations.

{question}""",
    }

    prompt = element_prompts.get(element, question)
    response, cost = call_single_model(prompt)
    return response, cost, {"method": f"structural_{element}"}


def run_additive_verification(question: str) -> tuple[str, float, dict]:
    """Additive verification: Always critique + conditional reasoning check."""
    total_cost = 0.0
    intermediates = {}

    # Step 1: Generate
    response, cost = call_single_model(question)
    total_cost += cost
    intermediates["initial"] = response[:500]

    # Step 2: Generic critique (always do this)
    critique_prompt = f"""Critique this response for factual accuracy and completeness.

Question: {question}
Response: {response}

Find specific issues."""

    critique, cost = call_single_model(critique_prompt)
    total_cost += cost
    intermediates["critique"] = critique[:500]

    # Step 3: Reasoning verification (always do this too - STACKED)
    reasoning_prompt = f"""Check the logical reasoning in this response.

Question: {question}
Response: {response}

For each inference:
1. Identify premise and conclusion
2. Check if conclusion follows logically
3. Flag any fallacies or gaps"""

    reasoning_check, cost = call_single_model(reasoning_prompt)
    total_cost += cost
    intermediates["reasoning_check"] = reasoning_check[:500]

    # Step 4: Revise with BOTH critiques (additive)
    revise_prompt = f"""Revise this response addressing both the factual critique AND the logical analysis.

Original question: {question}

Original response:
{response}

Factual critique:
{critique}

Logical analysis:
{reasoning_check}

Provide an improved response."""

    final, cost = call_single_model(revise_prompt, timeout=180)
    total_cost += cost

    return final, total_cost, {"method": "additive_verification", "intermediates": intermediates}


# ============ JUDGE ============

def run_judge(question: str, response: str, q_type: str, ground_truth: str = None) -> tuple[dict, float]:
    """LLM-as-Judge evaluation."""
    gt_section = f"\n\nGround truth: {ground_truth}" if ground_truth else ""

    prompt = f"""Evaluate this response on three dimensions (0-10 each):

Question: {question}
Type: {q_type}{gt_section}

Response:
{response}

1. STYLE (0-10): Depth, specificity, clarity, actionability
2. ADVERSARIAL (0-10): Would this survive fact-checking? Any fabrications?
3. REASONING (0-10): Logical structure, valid inferences

Output format:
STYLE_SCORE: [0-10]
ADVERSARIAL_SCORE: [0-10]
REASONING_SCORE: [0-10]
BRIEF_JUSTIFICATION: [2-3 sentences]"""

    result, cost = call_single_model(prompt, timeout=120)

    scores = {}
    for metric in ["STYLE", "ADVERSARIAL", "REASONING"]:
        match = re.search(rf'{metric}_SCORE:\s*(\d+)', result)
        scores[metric.lower()] = int(match.group(1)) if match else None

    match = re.search(r'BRIEF_JUSTIFICATION:\s*(.+?)$', result, re.DOTALL)
    scores["justification"] = match.group(1).strip()[:300] if match else ""

    return scores, cost


# ============ EXPERIMENT RUNNERS ============

def run_experiment_12A(state: dict, exp_id: str) -> dict:
    """Experiment 12A: Self-Consistency Sampling."""
    log(f"\n{'='*60}")
    log(f"EXPERIMENT 12A: Self-Consistency Sampling")
    log(f"{'='*60}")

    questions = EXPERIMENTS[exp_id]["questions"]
    results = {"runs": [], "summary": {}}

    for q_id in questions:
        q_data = QUESTIONS[q_id]
        question = q_data["question"]
        log(f"\nQuestion: {q_id}")

        # Run methods to compare
        methods = [
            ("baseline", lambda q: run_baseline(q)),
            ("rigor", lambda q: run_rigor(q)),
            ("self_consistency_k5", lambda q: run_self_consistency_k5(q)),
        ]

        for method_name, method_fn in methods:
            run_id = f"{exp_id}__{q_id}__{method_name}"

            if run_id in state["runs"] and state["runs"][run_id].get("complete"):
                log(f"  {method_name}: already done")
                continue

            log(f"  Running {method_name}...")
            response, cost, meta = method_fn(question)
            state["total_cost"] += cost

            # Judge
            scores, judge_cost = run_judge(question, response, q_data["type"], q_data.get("ground_truth"))
            state["total_cost"] += judge_cost

            run_data = {
                "experiment": exp_id,
                "question": q_id,
                "method": method_name,
                "response": response[:2000],
                "cost": cost,
                "scores": scores,
                "meta": meta,
                "complete": True
            }

            state["runs"][run_id] = run_data
            results["runs"].append(run_data)
            save_state(state)

            log(f"    S:{scores.get('style','?')} A:{scores.get('adversarial','?')} R:{scores.get('reasoning','?')}")
            time.sleep(2)

    return results


def run_experiment_8B(state: dict, exp_id: str) -> dict:
    """Experiment 8B: Anti-Fabrication Prompt."""
    log(f"\n{'='*60}")
    log(f"EXPERIMENT 8B: Anti-Fabrication Prompt")
    log(f"{'='*60}")

    questions = EXPERIMENTS[exp_id]["questions"]
    results = {"runs": [], "summary": {}}

    for q_id in questions:
        q_data = QUESTIONS[q_id]
        question = q_data["question"]
        log(f"\nQuestion: {q_id}")

        methods = [
            ("baseline", lambda q: run_baseline(q)),
            ("rigor", lambda q: run_rigor(q)),
            ("anti_fabrication", lambda q: run_anti_fabrication(q)),
        ]

        for method_name, method_fn in methods:
            run_id = f"{exp_id}__{q_id}__{method_name}"

            if run_id in state["runs"] and state["runs"][run_id].get("complete"):
                log(f"  {method_name}: already done")
                continue

            log(f"  Running {method_name}...")
            response, cost, meta = method_fn(question)
            state["total_cost"] += cost

            scores, judge_cost = run_judge(question, response, q_data["type"])
            state["total_cost"] += judge_cost

            run_data = {
                "experiment": exp_id,
                "question": q_id,
                "method": method_name,
                "response": response[:2000],
                "cost": cost,
                "scores": scores,
                "complete": True
            }

            state["runs"][run_id] = run_data
            results["runs"].append(run_data)
            save_state(state)

            log(f"    S:{scores.get('style','?')} A:{scores.get('adversarial','?')} R:{scores.get('reasoning','?')}")
            time.sleep(2)

    return results


def run_experiment_5A(state: dict, exp_id: str) -> dict:
    """Experiment 5A: Self-Critique on Multiple Question Types."""
    log(f"\n{'='*60}")
    log(f"EXPERIMENT 5A: Self-Critique Across Question Types")
    log(f"{'='*60}")

    questions = EXPERIMENTS[exp_id]["questions"]
    results = {"runs": [], "summary": {}}

    for q_id in questions:
        q_data = QUESTIONS[q_id]
        question = q_data["question"]
        log(f"\nQuestion: {q_id} (type: {q_data['type']})")

        methods = [
            ("baseline", lambda q: run_baseline(q)),
            ("rigor", lambda q: run_rigor(q)),
            ("self_critique", lambda q: run_self_critique(q)),
        ]

        for method_name, method_fn in methods:
            run_id = f"{exp_id}__{q_id}__{method_name}"

            if run_id in state["runs"] and state["runs"][run_id].get("complete"):
                log(f"  {method_name}: already done")
                continue

            log(f"  Running {method_name}...")
            response, cost, meta = method_fn(question)
            state["total_cost"] += cost

            scores, judge_cost = run_judge(question, response, q_data["type"], q_data.get("ground_truth"))
            state["total_cost"] += judge_cost

            run_data = {
                "experiment": exp_id,
                "question": q_id,
                "question_type": q_data["type"],
                "method": method_name,
                "response": response[:2000],
                "cost": cost,
                "scores": scores,
                "complete": True
            }

            state["runs"][run_id] = run_data
            results["runs"].append(run_data)
            save_state(state)

            log(f"    S:{scores.get('style','?')} A:{scores.get('adversarial','?')} R:{scores.get('reasoning','?')}")
            time.sleep(2)

    return results


def run_experiment_12B(state: dict, exp_id: str) -> dict:
    """Experiment 12B: Chain-of-Verification."""
    log(f"\n{'='*60}")
    log(f"EXPERIMENT 12B: Chain-of-Verification (Structured)")
    log(f"{'='*60}")

    questions = EXPERIMENTS[exp_id]["questions"]
    results = {"runs": [], "summary": {}}

    for q_id in questions:
        q_data = QUESTIONS[q_id]
        question = q_data["question"]
        log(f"\nQuestion: {q_id}")

        methods = [
            ("baseline", lambda q: run_baseline(q)),
            ("self_critique", lambda q: run_self_critique(q)),
            ("cove_structured", lambda q: run_cove_structured(q)),
        ]

        for method_name, method_fn in methods:
            run_id = f"{exp_id}__{q_id}__{method_name}"

            if run_id in state["runs"] and state["runs"][run_id].get("complete"):
                log(f"  {method_name}: already done")
                continue

            log(f"  Running {method_name}...")
            response, cost, meta = method_fn(question)
            state["total_cost"] += cost

            scores, judge_cost = run_judge(question, response, q_data["type"], q_data.get("ground_truth"))
            state["total_cost"] += judge_cost

            run_data = {
                "experiment": exp_id,
                "question": q_id,
                "method": method_name,
                "response": response[:2000],
                "cost": cost,
                "scores": scores,
                "complete": True
            }

            state["runs"][run_id] = run_data
            results["runs"].append(run_data)
            save_state(state)

            log(f"    S:{scores.get('style','?')} A:{scores.get('adversarial','?')} R:{scores.get('reasoning','?')}")
            time.sleep(2)

    return results


def run_experiment_6A(state: dict, exp_id: str) -> dict:
    """Experiment 6A: Prompt Engineering Combinations."""
    log(f"\n{'='*60}")
    log(f"EXPERIMENT 6A: Prompt Engineering Combinations")
    log(f"{'='*60}")

    questions = EXPERIMENTS[exp_id]["questions"]
    variants = ["baseline", "truth_aware", "citation", "thoroughness", "confidence", "combined"]
    results = {"runs": [], "summary": {}}

    for q_id in questions:
        q_data = QUESTIONS[q_id]
        question = q_data["question"]
        log(f"\nQuestion: {q_id}")

        for variant in variants:
            run_id = f"{exp_id}__{q_id}__prompt_{variant}"

            if run_id in state["runs"] and state["runs"][run_id].get("complete"):
                log(f"  {variant}: already done")
                continue

            log(f"  Running prompt variant: {variant}...")
            response, cost, meta = run_prompt_combo(question, variant)
            state["total_cost"] += cost

            scores, judge_cost = run_judge(question, response, q_data["type"])
            state["total_cost"] += judge_cost

            run_data = {
                "experiment": exp_id,
                "question": q_id,
                "method": f"prompt_{variant}",
                "variant": variant,
                "response": response[:2000],
                "cost": cost,
                "scores": scores,
                "complete": True
            }

            state["runs"][run_id] = run_data
            results["runs"].append(run_data)
            save_state(state)

            log(f"    S:{scores.get('style','?')} A:{scores.get('adversarial','?')} R:{scores.get('reasoning','?')}")
            time.sleep(2)

    return results


def run_experiment_10B(state: dict, exp_id: str) -> dict:
    """Experiment 10B: Structural Element Isolation."""
    log(f"\n{'='*60}")
    log(f"EXPERIMENT 10B: Structural Element Isolation")
    log(f"{'='*60}")

    questions = EXPERIMENTS[exp_id]["questions"]
    elements = ["disaggregation", "five_whys", "known_vs_contested", "eighty_twenty", "steelman", "what_wont_work"]
    results = {"runs": [], "summary": {}}

    for q_id in questions:
        q_data = QUESTIONS[q_id]
        question = q_data["question"]
        log(f"\nQuestion: {q_id}")

        # Baseline first
        run_id = f"{exp_id}__{q_id}__baseline"
        if run_id not in state["runs"] or not state["runs"][run_id].get("complete"):
            log(f"  Running baseline...")
            response, cost, meta = run_baseline(question)
            state["total_cost"] += cost
            scores, judge_cost = run_judge(question, response, q_data["type"])
            state["total_cost"] += judge_cost

            state["runs"][run_id] = {
                "experiment": exp_id, "question": q_id, "method": "baseline",
                "response": response[:2000], "cost": cost, "scores": scores, "complete": True
            }
            results["runs"].append(state["runs"][run_id])
            save_state(state)
            log(f"    S:{scores.get('style','?')} A:{scores.get('adversarial','?')} R:{scores.get('reasoning','?')}")
            time.sleep(2)

        # Each structural element
        for element in elements:
            run_id = f"{exp_id}__{q_id}__structural_{element}"

            if run_id in state["runs"] and state["runs"][run_id].get("complete"):
                log(f"  {element}: already done")
                continue

            log(f"  Running element: {element}...")
            response, cost, meta = run_structural_element(question, element)
            state["total_cost"] += cost

            scores, judge_cost = run_judge(question, response, q_data["type"])
            state["total_cost"] += judge_cost

            run_data = {
                "experiment": exp_id,
                "question": q_id,
                "method": f"structural_{element}",
                "element": element,
                "response": response[:2000],
                "cost": cost,
                "scores": scores,
                "complete": True
            }

            state["runs"][run_id] = run_data
            results["runs"].append(run_data)
            save_state(state)

            log(f"    S:{scores.get('style','?')} A:{scores.get('adversarial','?')} R:{scores.get('reasoning','?')}")
            time.sleep(2)

    return results


def run_additive_experiment(state: dict, exp_id: str) -> dict:
    """Additive Verification: Critique + Reasoning stacked."""
    log(f"\n{'='*60}")
    log(f"EXPERIMENT: Additive Verification")
    log(f"{'='*60}")

    questions = EXPERIMENTS[exp_id]["questions"]
    results = {"runs": [], "summary": {}}

    for q_id in questions:
        q_data = QUESTIONS[q_id]
        question = q_data["question"]
        log(f"\nQuestion: {q_id}")

        methods = [
            ("baseline", lambda q: run_baseline(q)),
            ("self_critique", lambda q: run_self_critique(q)),
            ("additive_verification", lambda q: run_additive_verification(q)),
        ]

        for method_name, method_fn in methods:
            run_id = f"{exp_id}__{q_id}__{method_name}"

            if run_id in state["runs"] and state["runs"][run_id].get("complete"):
                log(f"  {method_name}: already done")
                continue

            log(f"  Running {method_name}...")
            response, cost, meta = method_fn(question)
            state["total_cost"] += cost

            scores, judge_cost = run_judge(question, response, q_data["type"], q_data.get("ground_truth"))
            state["total_cost"] += judge_cost

            run_data = {
                "experiment": exp_id,
                "question": q_id,
                "method": method_name,
                "response": response[:2000],
                "cost": cost,
                "scores": scores,
                "complete": True
            }

            state["runs"][run_id] = run_data
            results["runs"].append(run_data)
            save_state(state)

            log(f"    S:{scores.get('style','?')} A:{scores.get('adversarial','?')} R:{scores.get('reasoning','?')}")
            time.sleep(2)

    return results


# ============ ANALYSIS ============

def analyze_all_results(state: dict):
    """Comprehensive analysis of all experiments."""
    log("\n" + "="*80)
    log("COMPREHENSIVE RESULTS ANALYSIS")
    log("="*80)

    all_results = {
        "by_experiment": {},
        "by_method": {},
        "total_cost": state["total_cost"],
        "total_runs": len([r for r in state["runs"].values() if r.get("complete")])
    }

    # Group by experiment
    for run_id, run in state["runs"].items():
        if not run.get("complete"):
            continue

        exp_id = run.get("experiment", "unknown")
        method = run.get("method", "unknown")
        scores = run.get("scores", {})

        # By experiment
        if exp_id not in all_results["by_experiment"]:
            all_results["by_experiment"][exp_id] = {"methods": {}}

        if method not in all_results["by_experiment"][exp_id]["methods"]:
            all_results["by_experiment"][exp_id]["methods"][method] = {
                "style": [], "adversarial": [], "reasoning": []
            }

        for metric in ["style", "adversarial", "reasoning"]:
            if scores.get(metric) is not None:
                all_results["by_experiment"][exp_id]["methods"][method][metric].append(scores[metric])

        # By method overall
        if method not in all_results["by_method"]:
            all_results["by_method"][method] = {"style": [], "adversarial": [], "reasoning": []}

        for metric in ["style", "adversarial", "reasoning"]:
            if scores.get(metric) is not None:
                all_results["by_method"][method][metric].append(scores[metric])

    # Print results by experiment
    for exp_id, exp_data in all_results["by_experiment"].items():
        log(f"\n=== {exp_id} ===")
        log(f"{'Method':<25} | {'Style':^7} | {'Adv':^7} | {'Reason':^7} | N")
        log("-" * 60)

        for method, data in sorted(exp_data["methods"].items()):
            avg_s = sum(data["style"])/len(data["style"]) if data["style"] else 0
            avg_a = sum(data["adversarial"])/len(data["adversarial"]) if data["adversarial"] else 0
            avg_r = sum(data["reasoning"])/len(data["reasoning"]) if data["reasoning"] else 0
            n = len(data["style"])
            log(f"{method:<25} | {avg_s:>5.1f}  | {avg_a:>5.1f}  | {avg_r:>5.1f}  | {n}")

    # Print overall method rankings
    log(f"\n{'='*80}")
    log("OVERALL METHOD RANKINGS (across all experiments)")
    log(f"{'='*80}")
    log(f"{'Method':<25} | {'Style':^7} | {'Adv':^7} | {'Reason':^7} | N")
    log("-" * 60)

    sorted_methods = sorted(
        all_results["by_method"].items(),
        key=lambda x: sum(x[1].get("adversarial", [0]))/max(len(x[1].get("adversarial", [1])), 1),
        reverse=True
    )

    for method, data in sorted_methods:
        avg_s = sum(data["style"])/len(data["style"]) if data["style"] else 0
        avg_a = sum(data["adversarial"])/len(data["adversarial"]) if data["adversarial"] else 0
        avg_r = sum(data["reasoning"])/len(data["reasoning"]) if data["reasoning"] else 0
        n = len(data["style"])
        log(f"{method:<25} | {avg_s:>5.1f}  | {avg_a:>5.1f}  | {avg_r:>5.1f}  | {n}")

    log(f"\n=== SUMMARY ===")
    log(f"Total runs completed: {all_results['total_runs']}")
    log(f"Total cost: ${state['total_cost']:.4f}")

    # Save results
    with open(RESULTS_FILE, "w") as f:
        json.dump(all_results, f, indent=2)
    log(f"\nResults saved to {RESULTS_FILE}")

    return all_results


# ============ MAIN ============

EXPERIMENT_RUNNERS = {
    "12A_self_consistency": run_experiment_12A,
    "8B_anti_fabrication": run_experiment_8B,
    "5A_self_critique_types": run_experiment_5A,
    "12B_cove": run_experiment_12B,
    "6A_prompt_combos": run_experiment_6A,
    "10B_structural_elements": run_experiment_10B,
    "additive_verification": run_additive_experiment,
}


def main():
    """Main entry point."""
    log("="*80)
    log("FULL EXPERIMENT BACKLOG RUNNER")
    log(f"Running {len(EXPERIMENTS)} experiments")
    log(f"Budget: ${BUDGET_LIMIT}")
    log("="*80)

    analyze_only = "--analyze" in sys.argv

    state = load_state()

    if analyze_only:
        analyze_all_results(state)
        return

    # Run each experiment
    for exp_id in EXPERIMENTS:
        if state["total_cost"] >= BUDGET_LIMIT:
            log(f"BUDGET LIMIT REACHED: ${state['total_cost']:.4f}", "WARN")
            break

        runner = EXPERIMENT_RUNNERS.get(exp_id)
        if runner:
            runner(state, exp_id)
        else:
            log(f"No runner for {exp_id}", "WARN")

    # Final analysis
    analyze_all_results(state)

    log("="*80)
    log("EXPERIMENT BACKLOG RUNNER COMPLETED")
    log(f"Total cost: ${state['total_cost']:.4f}")
    log("="*80)


if __name__ == "__main__":
    main()

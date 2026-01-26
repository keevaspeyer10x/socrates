#!/usr/bin/env python3
"""
Remaining Experiments Runner - All pending experiments from Issue #8

Pending:
- 5B: Cross-Model vs Self-Critique
- 6B: Self-Critique + Multi-Model
- 7A: Temperature Diversity
- 7B: Depth vs Breadth
- 8A: Minimal Effective Prompt
- 9: Real-World Question Battery (subset)
- 10A: Structured Thinking + Truth-Aware
- 10C: Self-Critique + Structured Thinking
- 11: Ask Models About Prompt Engineering
- 11B: Prompt Engineering Literature Review
- 12C: Agreement-as-Calibration
- 12D: Tool-Grounded Verification (simplified - no actual tools)
- 12E: Reasoning-Specific Verification

Usage:
    python3 experiments/runner_remaining.py           # Run all
    python3 experiments/runner_remaining.py --analyze # Analyze only
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
STATE_FILE = EXPERIMENTS_DIR / "experiment_state_remaining.json"
LOG_FILE = EXPERIMENTS_DIR / "experiment_remaining.log"
RESULTS_FILE = EXPERIMENTS_DIR / "experiment_results_remaining.json"
BUDGET_LIMIT = 150.0
RETRY_DELAY = 5
MAX_RETRIES = 3

# ============ TEST QUESTIONS ============

QUESTIONS = {
    # Factual
    "factual_1": {
        "type": "factual",
        "question": "What were the key technical causes of the 737 MAX crashes?",
    },
    "factual_2": {
        "type": "factual",
        "question": "What percentage of Fortune 500 CEOs have Harvard MBAs specifically? Cite your source.",
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
    },

    # Contested
    "contested_1": {
        "type": "contested",
        "question": "Should a 50-person engineering team at a growth-stage startup migrate from a Django monolith to microservices? They're experiencing scaling issues but have limited DevOps expertise.",
    },

    # Code architecture
    "code_1": {
        "type": "code",
        "question": "What's the best way to implement real-time collaboration in a document editor? Consider conflict resolution, latency, and scalability.",
    },

    # Prediction
    "prediction_1": {
        "type": "prediction",
        "question": "What will be the dominant AI model architecture in 2028?",
    },
}


def log(message: str, level: str = "INFO"):
    """Log to file and print."""
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
    """Call minds CLI."""
    cmd = ["minds", "ask"] + (args or []) + ["--yes", prompt]

    for attempt in range(MAX_RETRIES):
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            output = result.stdout.strip()

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
    """Single model baseline."""
    response, cost = call_single_model(question)
    return response, cost, {"method": "baseline"}


def run_self_critique(question: str, model: str = "gpt") -> tuple[str, float, dict]:
    """Generate → Critique → Revise with specified model."""
    total_cost = 0.0

    # Generate
    response, cost = call_single_model(question, model)
    total_cost += cost

    # Critique
    critique_prompt = f"""Critically evaluate this response for:
- Factual accuracy
- Logical reasoning
- Completeness

Question: {question}
Response: {response}

Provide specific critique."""

    critique, cost = call_single_model(critique_prompt, model)
    total_cost += cost

    # Revise
    revise_prompt = f"""Revise based on the critique.

Original question: {question}
Original response: {response}
Critique: {critique}

Provide improved response."""

    final, cost = call_single_model(revise_prompt, model)
    total_cost += cost

    return final, total_cost, {"method": f"self_critique_{model}"}


def run_cross_model_critique(question: str, generator: str, critiquer: str) -> tuple[str, float, dict]:
    """Generate with one model, critique with another."""
    total_cost = 0.0

    # Generate with generator
    response, cost = call_single_model(question, generator)
    total_cost += cost

    # Critique with critiquer
    critique_prompt = f"""Critically evaluate this response for accuracy and reasoning.

Question: {question}
Response: {response}

Provide specific critique."""

    critique, cost = call_single_model(critique_prompt, critiquer)
    total_cost += cost

    # Revise with generator
    revise_prompt = f"""Revise based on the critique.

Original question: {question}
Original response: {response}
Critique: {critique}

Provide improved response."""

    final, cost = call_single_model(revise_prompt, generator)
    total_cost += cost

    return final, total_cost, {"method": f"cross_critique_{generator}_{critiquer}"}


def run_multi_model_self_critique(question: str) -> tuple[str, float, dict]:
    """Each model self-critiques, then synthesize."""
    total_cost = 0.0
    critiqued_responses = []

    models = ["gpt", "claude", "gemini"]

    for model in models:
        # Each model generates and self-critiques
        response, cost, _ = run_self_critique(question, model)
        total_cost += cost
        critiqued_responses.append(f"[{model.upper()}]: {response}")
        time.sleep(1)

    # Synthesize
    synth_prompt = f"""Three models each generated and self-critiqued their responses.

Question: {question}

{chr(10).join(critiqued_responses)}

Synthesize the BEST answer, taking the strongest elements from each."""

    final, cost = call_single_model(synth_prompt, timeout=180)
    total_cost += cost

    return final, total_cost, {"method": "multi_model_self_critique"}


def run_temperature_diversity(question: str) -> tuple[str, float, dict]:
    """Same model, simulated different temperatures."""
    total_cost = 0.0
    responses = []

    prompts = [
        f"Answer precisely and deterministically:\n\n{question}",
        f"Answer with balanced analysis:\n\n{question}",
        f"Answer creatively, exploring unconventional angles:\n\n{question}",
    ]

    for i, prompt in enumerate(prompts):
        resp, cost = call_single_model(prompt)
        responses.append(resp)
        total_cost += cost
        time.sleep(1)

    # Synthesize
    synth_prompt = f"""Three responses with different approaches to the same question.

Question: {question}

PRECISE: {responses[0][:1500]}

BALANCED: {responses[1][:1500]}

CREATIVE: {responses[2][:1500]}

Synthesize the best answer."""

    final, cost = call_single_model(synth_prompt, timeout=180)
    total_cost += cost

    return final, total_cost, {"method": "temperature_diversity"}


def run_depth_vs_breadth_depth(question: str) -> tuple[str, float, dict]:
    """3 calls on one model (generate→critique→revise)."""
    return run_self_critique(question, "gpt")


def run_depth_vs_breadth_breadth(question: str) -> tuple[str, float, dict]:
    """3 different models, no critique."""
    total_cost = 0.0
    responses = []

    for model in ["gpt", "claude", "gemini"]:
        resp, cost = call_single_model(question, model)
        responses.append(f"[{model.upper()}]: {resp}")
        total_cost += cost
        time.sleep(1)

    # Synthesize
    synth_prompt = f"""Three different models answered:

Question: {question}

{chr(10).join(responses)}

Synthesize the best answer."""

    final, cost = call_single_model(synth_prompt, timeout=180)
    total_cost += cost

    return final, total_cost, {"method": "breadth_3models"}


def run_minimal_prompt_variant(question: str, variant: str) -> tuple[str, float, dict]:
    """Test minimal prompt variants."""
    prompts = {
        "baseline": question,
        "adversarial_only": f"Claims will be adversarially challenged.\n\n{question}",
        "no_absolutes_only": f"Avoid absolute language.\n\n{question}",
        "cite_only": f"Cite sources or acknowledge when you can't.\n\n{question}",
        "top_two": f"Claims will be adversarially challenged. Cite sources or acknowledge when you can't.\n\n{question}",
    }

    prompt = prompts.get(variant, question)
    response, cost = call_single_model(prompt)
    return response, cost, {"method": f"minimal_{variant}"}


def run_structured_truth_aware(question: str) -> tuple[str, float, dict]:
    """Combine structured thinking (v3) with truth-aware calibration."""
    prompt = f"""Answer this question using structured thinking AND truth-aware calibration.

STRUCTURE:
1. Break into sub-questions (disaggregation)
2. Identify the ONE factor that matters most (80/20)
3. Separate KNOWN (high confidence) from CONTESTED (genuine uncertainty)
4. Present strongest counterargument (steelman)

CALIBRATION:
- Claims will be adversarially challenged
- Avoid absolute language
- Cite sources or acknowledge uncertainty

Question: {question}"""

    response, cost = call_single_model(prompt, timeout=180)
    return response, cost, {"method": "structured_truth_aware"}


def run_self_critique_structured(question: str) -> tuple[str, float, dict]:
    """Self-critique with structured thinking lens."""
    total_cost = 0.0

    # Generate with structure
    gen_prompt = f"""Use structured thinking:
1. Disaggregate into sub-questions
2. Identify the 80/20 factor
3. Separate known from contested

{question}"""

    response, cost = call_single_model(gen_prompt, timeout=180)
    total_cost += cost

    # Critique with structured lens
    critique_prompt = f"""Critique this response using structured thinking criteria:
- Did it properly disaggregate?
- Did it identify the real crux (80/20)?
- Did it separate known from contested?
- Any logical gaps?

Response: {response}

Provide specific structural critique."""

    critique, cost = call_single_model(critique_prompt)
    total_cost += cost

    # Revise
    revise_prompt = f"""Revise based on structural critique.

Original question: {question}
Original response: {response}
Critique: {critique}

Provide structurally improved response."""

    final, cost = call_single_model(revise_prompt, timeout=180)
    total_cost += cost

    return final, total_cost, {"method": "self_critique_structured"}


def run_agreement_as_calibration(question: str) -> tuple[str, float, dict]:
    """Multi-model with explicit agreement tracking."""
    total_cost = 0.0
    responses = []

    for model in ["gpt", "claude", "gemini"]:
        resp, cost = call_single_model(question, model)
        responses.append({"model": model, "response": resp})
        total_cost += cost
        time.sleep(1)

    # Analyze agreement
    agreement_prompt = f"""Analyze agreement across these 3 model responses.

Question: {question}

GPT: {responses[0]['response'][:1500]}

CLAUDE: {responses[1]['response'][:1500]}

GEMINI: {responses[2]['response'][:1500]}

Output:
1. CONSENSUS CLAIMS (all 3 agree): List them
2. MAJORITY CLAIMS (2/3 agree): List them with which model disagrees
3. CONTESTED CLAIMS (no agreement): List the different positions
4. FINAL ANSWER: Synthesize, marking confidence based on agreement level"""

    final, cost = call_single_model(agreement_prompt, timeout=180)
    total_cost += cost

    return final, total_cost, {"method": "agreement_calibration"}


def run_reasoning_verification(question: str) -> tuple[str, float, dict]:
    """Explicit logic checking."""
    total_cost = 0.0

    # Generate with explicit reasoning
    gen_prompt = f"""Answer with explicit step-by-step reasoning. Number each logical step.

{question}"""

    response, cost = call_single_model(gen_prompt)
    total_cost += cost

    # Verify reasoning
    verify_prompt = f"""Check each reasoning step for logical validity.

For each step:
1. Identify premise and conclusion
2. Check if conclusion follows logically
3. Flag any fallacies (false dichotomy, hasty generalization, circular reasoning, etc.)
4. Check for unsupported assumptions

Response to verify: {response}

Provide step-by-step verification."""

    verification, cost = call_single_model(verify_prompt)
    total_cost += cost

    # Revise
    revise_prompt = f"""Revise based on logical verification.

Original question: {question}
Original response: {response}
Verification: {verification}

Provide logically sound response."""

    final, cost = call_single_model(revise_prompt)
    total_cost += cost

    return final, total_cost, {"method": "reasoning_verification"}


def run_tool_grounded_critique(question: str) -> tuple[str, float, dict]:
    """Self-critique with explicit citation verification instruction."""
    total_cost = 0.0

    # Generate
    response, cost = call_single_model(question)
    total_cost += cost

    # Critique with grounding instruction
    critique_prompt = f"""Critique this response with GROUNDING requirements:

For each factual claim:
1. Can you verify this from your training data?
2. If citing a source, does it actually exist and say this?
3. If you're uncertain, mark as UNVERIFIED

Question: {question}
Response: {response}

Provide grounded critique - mark each claim as VERIFIED, UNVERIFIED, or UNCERTAIN."""

    critique, cost = call_single_model(critique_prompt)
    total_cost += cost

    # Revise
    revise_prompt = f"""Revise, removing or qualifying UNVERIFIED claims.

Original question: {question}
Original response: {response}
Grounded critique: {critique}

Provide response with only verified or appropriately qualified claims."""

    final, cost = call_single_model(revise_prompt)
    total_cost += cost

    return final, total_cost, {"method": "tool_grounded_critique"}


def run_meta_prompt_research(question: str = None) -> tuple[str, float, dict]:
    """Ask models about prompt engineering research."""
    meta_question = """What are the most effective prompt engineering techniques for getting accurate, well-calibrated responses from LLMs?

Based on research and documented techniques:
1. What techniques have the strongest evidence for improving accuracy?
2. What techniques help with calibration (appropriate confidence)?
3. What techniques reduce hallucination/fabrication?
4. What are common failure modes of prompting?

Cite specific research or documented best practices where possible."""

    response, cost = call_minds(meta_question, ["--rigor"], timeout=300)
    return response, cost, {"method": "meta_prompt_research"}


def run_literature_review(topic: str) -> tuple[str, float, dict]:
    """Deep dive on specific technique."""
    prompt = f"""Research deep dive: {topic}

Provide:
1. Key papers/sources on this technique
2. How it works mechanistically
3. When it helps vs when it doesn't
4. How to implement it effectively
5. Known limitations

Be specific and cite sources where possible."""

    response, cost = call_minds(prompt, ["--rigor"], timeout=300)
    return response, cost, {"method": f"literature_{topic.replace(' ', '_')[:20]}"}


# ============ JUDGE ============

def run_judge(question: str, response: str, q_type: str, ground_truth: str = None) -> tuple[dict, float]:
    """LLM-as-Judge evaluation."""
    gt_section = f"\n\nGround truth: {ground_truth}" if ground_truth else ""

    prompt = f"""Evaluate this response (0-10 each):

Question: {question}
Type: {q_type}{gt_section}

Response:
{response}

1. STYLE (0-10): Depth, specificity, clarity
2. ADVERSARIAL (0-10): Would this survive fact-checking?
3. REASONING (0-10): Logical structure

Output:
STYLE_SCORE: [0-10]
ADVERSARIAL_SCORE: [0-10]
REASONING_SCORE: [0-10]
JUSTIFICATION: [1-2 sentences]"""

    result, cost = call_single_model(prompt, timeout=120)

    scores = {}
    for metric in ["STYLE", "ADVERSARIAL", "REASONING"]:
        match = re.search(rf'{metric}_SCORE:\s*(\d+)', result)
        scores[metric.lower()] = int(match.group(1)) if match else None

    return scores, cost


# ============ EXPERIMENT RUNNERS ============

def run_experiment_5B(state: dict) -> dict:
    """Cross-Model vs Self-Critique."""
    log(f"\n{'='*60}")
    log("EXPERIMENT 5B: Cross-Model vs Self-Critique")
    log(f"{'='*60}")

    questions = ["factual_1", "reasoning_2", "contested_1"]

    for q_id in questions:
        q_data = QUESTIONS[q_id]
        question = q_data["question"]
        log(f"\nQuestion: {q_id}")

        # Test configurations
        configs = [
            ("self_critique_gpt", lambda q: run_self_critique(q, "gpt")),
            ("cross_gpt_claude", lambda q: run_cross_model_critique(q, "gpt", "claude")),
            ("cross_gpt_gemini", lambda q: run_cross_model_critique(q, "gpt", "gemini")),
        ]

        for method_name, method_fn in configs:
            run_id = f"5B__{q_id}__{method_name}"

            if run_id in state["runs"] and state["runs"][run_id].get("complete"):
                log(f"  {method_name}: already done")
                continue

            log(f"  Running {method_name}...")
            response, cost, meta = method_fn(question)
            state["total_cost"] += cost

            scores, judge_cost = run_judge(question, response, q_data["type"], q_data.get("ground_truth"))
            state["total_cost"] += judge_cost

            state["runs"][run_id] = {
                "experiment": "5B",
                "question": q_id,
                "method": method_name,
                "response": response[:2000],
                "cost": cost,
                "scores": scores,
                "complete": True
            }
            save_state(state)

            log(f"    S:{scores.get('style','?')} A:{scores.get('adversarial','?')} R:{scores.get('reasoning','?')}")
            time.sleep(2)


def run_experiment_6B(state: dict) -> dict:
    """Self-Critique + Multi-Model."""
    log(f"\n{'='*60}")
    log("EXPERIMENT 6B: Self-Critique + Multi-Model")
    log(f"{'='*60}")

    questions = ["factual_1", "contested_1"]

    for q_id in questions:
        q_data = QUESTIONS[q_id]
        question = q_data["question"]
        log(f"\nQuestion: {q_id}")

        configs = [
            ("baseline", lambda q: run_baseline(q)),
            ("self_critique_solo", lambda q: run_self_critique(q, "gpt")),
            ("multi_model_self_critique", lambda q: run_multi_model_self_critique(q)),
        ]

        for method_name, method_fn in configs:
            run_id = f"6B__{q_id}__{method_name}"

            if run_id in state["runs"] and state["runs"][run_id].get("complete"):
                log(f"  {method_name}: already done")
                continue

            log(f"  Running {method_name}...")
            response, cost, meta = method_fn(question)
            state["total_cost"] += cost

            scores, judge_cost = run_judge(question, response, q_data["type"])
            state["total_cost"] += judge_cost

            state["runs"][run_id] = {
                "experiment": "6B",
                "question": q_id,
                "method": method_name,
                "response": response[:2000],
                "cost": cost,
                "scores": scores,
                "complete": True
            }
            save_state(state)

            log(f"    S:{scores.get('style','?')} A:{scores.get('adversarial','?')} R:{scores.get('reasoning','?')}")
            time.sleep(2)


def run_experiment_7A(state: dict) -> dict:
    """Temperature Diversity."""
    log(f"\n{'='*60}")
    log("EXPERIMENT 7A: Temperature Diversity")
    log(f"{'='*60}")

    questions = ["factual_1", "reasoning_2", "contested_1"]

    for q_id in questions:
        q_data = QUESTIONS[q_id]
        question = q_data["question"]
        log(f"\nQuestion: {q_id}")

        configs = [
            ("baseline", lambda q: run_baseline(q)),
            ("temperature_diversity", lambda q: run_temperature_diversity(q)),
        ]

        for method_name, method_fn in configs:
            run_id = f"7A__{q_id}__{method_name}"

            if run_id in state["runs"] and state["runs"][run_id].get("complete"):
                log(f"  {method_name}: already done")
                continue

            log(f"  Running {method_name}...")
            response, cost, meta = method_fn(question)
            state["total_cost"] += cost

            scores, judge_cost = run_judge(question, response, q_data["type"])
            state["total_cost"] += judge_cost

            state["runs"][run_id] = {
                "experiment": "7A",
                "question": q_id,
                "method": method_name,
                "response": response[:2000],
                "cost": cost,
                "scores": scores,
                "complete": True
            }
            save_state(state)

            log(f"    S:{scores.get('style','?')} A:{scores.get('adversarial','?')} R:{scores.get('reasoning','?')}")
            time.sleep(2)


def run_experiment_7B(state: dict) -> dict:
    """Depth vs Breadth."""
    log(f"\n{'='*60}")
    log("EXPERIMENT 7B: Depth vs Breadth (same token budget)")
    log(f"{'='*60}")

    questions = ["factual_1", "reasoning_2", "contested_1"]

    for q_id in questions:
        q_data = QUESTIONS[q_id]
        question = q_data["question"]
        log(f"\nQuestion: {q_id}")

        configs = [
            ("depth_self_critique", lambda q: run_depth_vs_breadth_depth(q)),
            ("breadth_3_models", lambda q: run_depth_vs_breadth_breadth(q)),
        ]

        for method_name, method_fn in configs:
            run_id = f"7B__{q_id}__{method_name}"

            if run_id in state["runs"] and state["runs"][run_id].get("complete"):
                log(f"  {method_name}: already done")
                continue

            log(f"  Running {method_name}...")
            response, cost, meta = method_fn(question)
            state["total_cost"] += cost

            scores, judge_cost = run_judge(question, response, q_data["type"])
            state["total_cost"] += judge_cost

            state["runs"][run_id] = {
                "experiment": "7B",
                "question": q_id,
                "method": method_name,
                "response": response[:2000],
                "cost": cost,
                "scores": scores,
                "complete": True
            }
            save_state(state)

            log(f"    S:{scores.get('style','?')} A:{scores.get('adversarial','?')} R:{scores.get('reasoning','?')}")
            time.sleep(2)


def run_experiment_8A(state: dict) -> dict:
    """Minimal Effective Prompt."""
    log(f"\n{'='*60}")
    log("EXPERIMENT 8A: Minimal Effective Prompt")
    log(f"{'='*60}")

    questions = ["factual_2", "contested_1"]  # factual_2 is the hallucination-prone one
    variants = ["baseline", "adversarial_only", "no_absolutes_only", "cite_only", "top_two"]

    for q_id in questions:
        q_data = QUESTIONS[q_id]
        question = q_data["question"]
        log(f"\nQuestion: {q_id}")

        for variant in variants:
            run_id = f"8A__{q_id}__minimal_{variant}"

            if run_id in state["runs"] and state["runs"][run_id].get("complete"):
                log(f"  {variant}: already done")
                continue

            log(f"  Running variant: {variant}...")
            response, cost, meta = run_minimal_prompt_variant(question, variant)
            state["total_cost"] += cost

            scores, judge_cost = run_judge(question, response, q_data["type"])
            state["total_cost"] += judge_cost

            state["runs"][run_id] = {
                "experiment": "8A",
                "question": q_id,
                "method": f"minimal_{variant}",
                "variant": variant,
                "response": response[:2000],
                "cost": cost,
                "scores": scores,
                "complete": True
            }
            save_state(state)

            log(f"    S:{scores.get('style','?')} A:{scores.get('adversarial','?')} R:{scores.get('reasoning','?')}")
            time.sleep(2)


def run_experiment_10A(state: dict) -> dict:
    """Structured Thinking + Truth-Aware."""
    log(f"\n{'='*60}")
    log("EXPERIMENT 10A: Structured Thinking + Truth-Aware")
    log(f"{'='*60}")

    questions = ["contested_1", "reasoning_2"]

    for q_id in questions:
        q_data = QUESTIONS[q_id]
        question = q_data["question"]
        log(f"\nQuestion: {q_id}")

        configs = [
            ("baseline", lambda q: run_baseline(q)),
            ("structured_truth_aware", lambda q: run_structured_truth_aware(q)),
        ]

        for method_name, method_fn in configs:
            run_id = f"10A__{q_id}__{method_name}"

            if run_id in state["runs"] and state["runs"][run_id].get("complete"):
                log(f"  {method_name}: already done")
                continue

            log(f"  Running {method_name}...")
            response, cost, meta = method_fn(question)
            state["total_cost"] += cost

            scores, judge_cost = run_judge(question, response, q_data["type"])
            state["total_cost"] += judge_cost

            state["runs"][run_id] = {
                "experiment": "10A",
                "question": q_id,
                "method": method_name,
                "response": response[:2000],
                "cost": cost,
                "scores": scores,
                "complete": True
            }
            save_state(state)

            log(f"    S:{scores.get('style','?')} A:{scores.get('adversarial','?')} R:{scores.get('reasoning','?')}")
            time.sleep(2)


def run_experiment_10C(state: dict) -> dict:
    """Self-Critique + Structured Thinking."""
    log(f"\n{'='*60}")
    log("EXPERIMENT 10C: Self-Critique + Structured Thinking")
    log(f"{'='*60}")

    questions = ["contested_1", "reasoning_2"]

    for q_id in questions:
        q_data = QUESTIONS[q_id]
        question = q_data["question"]
        log(f"\nQuestion: {q_id}")

        configs = [
            ("baseline", lambda q: run_baseline(q)),
            ("self_critique", lambda q: run_self_critique(q, "gpt")),
            ("self_critique_structured", lambda q: run_self_critique_structured(q)),
        ]

        for method_name, method_fn in configs:
            run_id = f"10C__{q_id}__{method_name}"

            if run_id in state["runs"] and state["runs"][run_id].get("complete"):
                log(f"  {method_name}: already done")
                continue

            log(f"  Running {method_name}...")
            response, cost, meta = method_fn(question)
            state["total_cost"] += cost

            scores, judge_cost = run_judge(question, response, q_data["type"])
            state["total_cost"] += judge_cost

            state["runs"][run_id] = {
                "experiment": "10C",
                "question": q_id,
                "method": method_name,
                "response": response[:2000],
                "cost": cost,
                "scores": scores,
                "complete": True
            }
            save_state(state)

            log(f"    S:{scores.get('style','?')} A:{scores.get('adversarial','?')} R:{scores.get('reasoning','?')}")
            time.sleep(2)


def run_experiment_12C(state: dict) -> dict:
    """Agreement-as-Calibration."""
    log(f"\n{'='*60}")
    log("EXPERIMENT 12C: Agreement-as-Calibration")
    log(f"{'='*60}")

    questions = ["factual_1", "factual_2", "contested_1"]

    for q_id in questions:
        q_data = QUESTIONS[q_id]
        question = q_data["question"]
        log(f"\nQuestion: {q_id}")

        configs = [
            ("baseline", lambda q: run_baseline(q)),
            ("agreement_calibration", lambda q: run_agreement_as_calibration(q)),
        ]

        for method_name, method_fn in configs:
            run_id = f"12C__{q_id}__{method_name}"

            if run_id in state["runs"] and state["runs"][run_id].get("complete"):
                log(f"  {method_name}: already done")
                continue

            log(f"  Running {method_name}...")
            response, cost, meta = method_fn(question)
            state["total_cost"] += cost

            scores, judge_cost = run_judge(question, response, q_data["type"])
            state["total_cost"] += judge_cost

            state["runs"][run_id] = {
                "experiment": "12C",
                "question": q_id,
                "method": method_name,
                "response": response[:2000],
                "cost": cost,
                "scores": scores,
                "complete": True
            }
            save_state(state)

            log(f"    S:{scores.get('style','?')} A:{scores.get('adversarial','?')} R:{scores.get('reasoning','?')}")
            time.sleep(2)


def run_experiment_12D(state: dict) -> dict:
    """Tool-Grounded Verification (simplified)."""
    log(f"\n{'='*60}")
    log("EXPERIMENT 12D: Tool-Grounded Verification")
    log(f"{'='*60}")

    questions = ["factual_1", "factual_2"]

    for q_id in questions:
        q_data = QUESTIONS[q_id]
        question = q_data["question"]
        log(f"\nQuestion: {q_id}")

        configs = [
            ("baseline", lambda q: run_baseline(q)),
            ("self_critique", lambda q: run_self_critique(q, "gpt")),
            ("tool_grounded_critique", lambda q: run_tool_grounded_critique(q)),
        ]

        for method_name, method_fn in configs:
            run_id = f"12D__{q_id}__{method_name}"

            if run_id in state["runs"] and state["runs"][run_id].get("complete"):
                log(f"  {method_name}: already done")
                continue

            log(f"  Running {method_name}...")
            response, cost, meta = method_fn(question)
            state["total_cost"] += cost

            scores, judge_cost = run_judge(question, response, q_data["type"])
            state["total_cost"] += judge_cost

            state["runs"][run_id] = {
                "experiment": "12D",
                "question": q_id,
                "method": method_name,
                "response": response[:2000],
                "cost": cost,
                "scores": scores,
                "complete": True
            }
            save_state(state)

            log(f"    S:{scores.get('style','?')} A:{scores.get('adversarial','?')} R:{scores.get('reasoning','?')}")
            time.sleep(2)


def run_experiment_12E(state: dict) -> dict:
    """Reasoning-Specific Verification."""
    log(f"\n{'='*60}")
    log("EXPERIMENT 12E: Reasoning-Specific Verification")
    log(f"{'='*60}")

    questions = ["reasoning_1", "reasoning_2", "contested_1"]

    for q_id in questions:
        q_data = QUESTIONS[q_id]
        question = q_data["question"]
        log(f"\nQuestion: {q_id}")

        configs = [
            ("baseline", lambda q: run_baseline(q)),
            ("self_critique", lambda q: run_self_critique(q, "gpt")),
            ("reasoning_verification", lambda q: run_reasoning_verification(q)),
        ]

        for method_name, method_fn in configs:
            run_id = f"12E__{q_id}__{method_name}"

            if run_id in state["runs"] and state["runs"][run_id].get("complete"):
                log(f"  {method_name}: already done")
                continue

            log(f"  Running {method_name}...")
            response, cost, meta = method_fn(question)
            state["total_cost"] += cost

            scores, judge_cost = run_judge(question, response, q_data["type"], q_data.get("ground_truth"))
            state["total_cost"] += judge_cost

            state["runs"][run_id] = {
                "experiment": "12E",
                "question": q_id,
                "method": method_name,
                "response": response[:2000],
                "cost": cost,
                "scores": scores,
                "complete": True
            }
            save_state(state)

            log(f"    S:{scores.get('style','?')} A:{scores.get('adversarial','?')} R:{scores.get('reasoning','?')}")
            time.sleep(2)


def run_experiment_11(state: dict) -> dict:
    """Meta: Ask Models About Prompt Engineering."""
    log(f"\n{'='*60}")
    log("EXPERIMENT 11: Meta Prompt Engineering Research")
    log(f"{'='*60}")

    run_id = "11__meta_prompt_research"

    if run_id in state["runs"] and state["runs"][run_id].get("complete"):
        log("  Already done")
        return

    log("  Running meta prompt research with --rigor...")
    response, cost, meta = run_meta_prompt_research()
    state["total_cost"] += cost

    state["runs"][run_id] = {
        "experiment": "11",
        "method": "meta_prompt_research",
        "response": response[:4000],
        "cost": cost,
        "complete": True
    }
    save_state(state)

    log(f"  Done. Response length: {len(response)} chars")


def run_experiment_11B(state: dict) -> dict:
    """Literature Review on Key Techniques."""
    log(f"\n{'='*60}")
    log("EXPERIMENT 11B: Literature Review")
    log(f"{'='*60}")

    topics = [
        "chain of thought prompting",
        "self-consistency majority voting",
        "Constitutional AI principle-based prompting",
    ]

    for topic in topics:
        run_id = f"11B__literature_{topic.replace(' ', '_')[:15]}"

        if run_id in state["runs"] and state["runs"][run_id].get("complete"):
            log(f"  {topic}: already done")
            continue

        log(f"  Researching: {topic}...")
        response, cost, meta = run_literature_review(topic)
        state["total_cost"] += cost

        state["runs"][run_id] = {
            "experiment": "11B",
            "topic": topic,
            "method": "literature_review",
            "response": response[:4000],
            "cost": cost,
            "complete": True
        }
        save_state(state)

        log(f"  Done. Response length: {len(response)} chars")
        time.sleep(2)


# ============ ANALYSIS ============

def analyze_results(state: dict):
    """Comprehensive analysis."""
    log("\n" + "="*80)
    log("COMPREHENSIVE RESULTS ANALYSIS")
    log("="*80)

    results = {
        "by_experiment": {},
        "by_method": {},
        "total_cost": state["total_cost"],
        "total_runs": len([r for r in state["runs"].values() if r.get("complete") and r.get("scores")])
    }

    # Group by experiment
    for run_id, run in state["runs"].items():
        if not run.get("complete") or not run.get("scores"):
            continue

        exp_id = run.get("experiment", "unknown")
        method = run.get("method", "unknown")
        scores = run.get("scores", {})

        if exp_id not in results["by_experiment"]:
            results["by_experiment"][exp_id] = {"methods": {}}

        if method not in results["by_experiment"][exp_id]["methods"]:
            results["by_experiment"][exp_id]["methods"][method] = {
                "style": [], "adversarial": [], "reasoning": []
            }

        for metric in ["style", "adversarial", "reasoning"]:
            if scores.get(metric) is not None:
                results["by_experiment"][exp_id]["methods"][method][metric].append(scores[metric])

        # Overall by method
        if method not in results["by_method"]:
            results["by_method"][method] = {"style": [], "adversarial": [], "reasoning": []}

        for metric in ["style", "adversarial", "reasoning"]:
            if scores.get(metric) is not None:
                results["by_method"][method][metric].append(scores[metric])

    # Print by experiment
    for exp_id, exp_data in sorted(results["by_experiment"].items()):
        log(f"\n=== {exp_id} ===")
        log(f"{'Method':<30} | {'Style':^7} | {'Adv':^7} | {'Reason':^7} | N")
        log("-" * 70)

        for method, data in sorted(exp_data["methods"].items()):
            avg_s = sum(data["style"])/len(data["style"]) if data["style"] else 0
            avg_a = sum(data["adversarial"])/len(data["adversarial"]) if data["adversarial"] else 0
            avg_r = sum(data["reasoning"])/len(data["reasoning"]) if data["reasoning"] else 0
            n = len(data["style"])
            log(f"{method:<30} | {avg_s:>5.1f}  | {avg_a:>5.1f}  | {avg_r:>5.1f}  | {n}")

    # Overall rankings
    log(f"\n{'='*80}")
    log("OVERALL METHOD RANKINGS")
    log(f"{'='*80}")
    log(f"{'Method':<30} | {'Style':^7} | {'Adv':^7} | {'Reason':^7} | {'Avg':^7} | N")
    log("-" * 80)

    sorted_methods = []
    for method, data in results["by_method"].items():
        avg_s = sum(data["style"])/len(data["style"]) if data["style"] else 0
        avg_a = sum(data["adversarial"])/len(data["adversarial"]) if data["adversarial"] else 0
        avg_r = sum(data["reasoning"])/len(data["reasoning"]) if data["reasoning"] else 0
        avg_all = (avg_s + avg_a + avg_r) / 3
        n = len(data["style"])
        sorted_methods.append((method, avg_s, avg_a, avg_r, avg_all, n))

    for method, avg_s, avg_a, avg_r, avg_all, n in sorted(sorted_methods, key=lambda x: x[4], reverse=True):
        log(f"{method:<30} | {avg_s:>5.1f}  | {avg_a:>5.1f}  | {avg_r:>5.1f}  | {avg_all:>5.1f}  | {n}")

    log(f"\n=== SUMMARY ===")
    log(f"Total runs: {results['total_runs']}")
    log(f"Total cost: ${state['total_cost']:.4f}")

    with open(RESULTS_FILE, "w") as f:
        json.dump(results, f, indent=2)
    log(f"\nResults saved to {RESULTS_FILE}")

    return results


# ============ MAIN ============

EXPERIMENT_RUNNERS = {
    "5B": run_experiment_5B,
    "6B": run_experiment_6B,
    "7A": run_experiment_7A,
    "7B": run_experiment_7B,
    "8A": run_experiment_8A,
    "10A": run_experiment_10A,
    "10C": run_experiment_10C,
    "11": run_experiment_11,
    "11B": run_experiment_11B,
    "12C": run_experiment_12C,
    "12D": run_experiment_12D,
    "12E": run_experiment_12E,
}


def main():
    """Main entry point."""
    log("="*80)
    log("REMAINING EXPERIMENTS RUNNER")
    log(f"Running {len(EXPERIMENT_RUNNERS)} experiments")
    log(f"Budget: ${BUDGET_LIMIT}")
    log("="*80)

    analyze_only = "--analyze" in sys.argv

    state = load_state()

    if analyze_only:
        analyze_results(state)
        return

    # Run experiments in order
    experiment_order = ["5B", "6B", "7A", "7B", "8A", "10A", "10C", "12C", "12D", "12E", "11", "11B"]

    for exp_id in experiment_order:
        if state["total_cost"] >= BUDGET_LIMIT:
            log(f"BUDGET LIMIT REACHED: ${state['total_cost']:.4f}", "WARN")
            break

        runner = EXPERIMENT_RUNNERS.get(exp_id)
        if runner:
            log(f"\n{'#'*60}")
            log(f"Starting experiment {exp_id}")
            log(f"Budget: ${state['total_cost']:.4f} / ${BUDGET_LIMIT}")
            log(f"{'#'*60}")
            runner(state)

    analyze_results(state)

    log("="*80)
    log("REMAINING EXPERIMENTS RUNNER COMPLETED")
    log(f"Total cost: ${state['total_cost']:.4f}")
    log("="*80)


if __name__ == "__main__":
    main()

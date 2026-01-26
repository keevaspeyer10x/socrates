#!/usr/bin/env python3
"""
Full Stack Verification Experiment

Tests comprehensive pipeline combining:
1. Best prompt learnings
2. Multi-model generation
3. Self-critique + verification + reasoning checks
4. Informed integration with guidance
5. Final critique by strongest model

Run on HARD questions where baseline fails.
"""

import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

EXPERIMENTS_DIR = Path(__file__).parent
LOG_FILE = EXPERIMENTS_DIR / "experiment_fullstack.log"
RESULTS_FILE = EXPERIMENTS_DIR / "experiment_results_fullstack.json"

# Hard questions where baseline adversarial ≤ 6
HARD_QUESTIONS = {
    "factual_fabrication": {
        "question": "What percentage of Fortune 500 CEOs have Harvard MBAs specifically? Cite your source.",
        "type": "factual",
        "baseline_adv": 3,  # From 8B experiment
        "notes": "Models tend to fabricate specific statistics"
    },
    "factual_complex": {
        "question": "What were the key technical causes of the 2024 CrowdStrike outage that affected millions of Windows computers?",
        "type": "factual",
        "baseline_adv": 5,  # Estimated - recent event, easy to hallucinate
        "notes": "Recent event with specific technical details"
    },
    "contested_nuanced": {
        "question": "Should a 50-person engineering team at a growth-stage startup migrate from a Django monolith to microservices? They're experiencing scaling issues but have limited DevOps expertise.",
        "type": "contested",
        "baseline_adv": 6,  # From 12D experiment
        "notes": "Requires nuanced tradeoff analysis"
    },
}


def log(message: str, level: str = "INFO"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] [{level}] {message}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")


def call_model(prompt: str, model: str = "gpt", timeout: int = 180) -> tuple[str, float]:
    """Call a specific model via minds CLI."""
    cmd = ["minds", "ask", "--model", model, "--yes", prompt]

    for attempt in range(3):
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
                log(f"Empty response from {model}, retry {attempt+1}/3", "WARN")
                time.sleep(3)
        except subprocess.TimeoutExpired:
            log(f"Timeout from {model}, retry {attempt+1}/3", "WARN")
            time.sleep(5)
        except Exception as e:
            log(f"Error from {model}: {e}", "ERROR")
            time.sleep(3)

    return "", 0.0


def run_judge(question: str, response: str, q_type: str) -> tuple[dict, float]:
    """LLM-as-Judge evaluation."""
    prompt = f"""Evaluate this response on a 0-10 scale for each dimension.

Question: {question}
Question Type: {q_type}

Response to evaluate:
{response[:3000]}

Scoring criteria:
- STYLE (0-10): Depth of analysis, specificity, clarity of communication
- ADVERSARIAL (0-10): Would this survive rigorous fact-checking? Are claims verifiable? Is confidence calibrated to evidence?
- REASONING (0-10): Logical structure, valid inferences, appropriate handling of uncertainty

Be harsh on:
- Confident-sounding claims without evidence
- Fabricated statistics or citations
- False precision when uncertainty is warranted

Output format (exactly):
STYLE_SCORE: [0-10]
ADVERSARIAL_SCORE: [0-10]
REASONING_SCORE: [0-10]
JUSTIFICATION: [2-3 sentences explaining scores]"""

    result, cost = call_model(prompt, "claude", timeout=120)

    scores = {}
    for metric in ["STYLE", "ADVERSARIAL", "REASONING"]:
        match = re.search(rf'{metric}_SCORE:\s*(\d+)', result)
        scores[metric.lower()] = int(match.group(1)) if match else None

    # Extract justification
    just_match = re.search(r'JUSTIFICATION:\s*(.+)', result, re.DOTALL)
    scores['justification'] = just_match.group(1).strip()[:500] if just_match else ""

    return scores, cost


# ============ METHOD IMPLEMENTATIONS ============

def run_baseline(question: str) -> tuple[str, float, dict]:
    """Plain single model, no enhancements."""
    response, cost = call_model(question, "gpt")
    return response, cost, {"method": "baseline", "steps": 1}


def run_anti_fabrication_only(question: str) -> tuple[str, float, dict]:
    """Just the anti-fabrication prompt."""
    prompt = f"""Answer this question. Important guidelines:
- If you're not certain about something, say so explicitly
- Do not fabricate statistics, citations, or specific claims
- It's better to acknowledge uncertainty than to sound confident incorrectly

Question: {question}"""

    response, cost = call_model(prompt, "gpt")
    return response, cost, {"method": "anti_fab_only", "steps": 1}


def run_self_critique(question: str) -> tuple[str, float, dict]:
    """Standard self-critique (from our winning methods)."""
    total_cost = 0.0

    # Generate
    response, cost = call_model(question, "gpt")
    total_cost += cost

    # Critique
    critique_prompt = f"""Critically evaluate this response:

Question: {question}
Response: {response}

What might be wrong? What claims are you uncertain about? What would a skeptic challenge?"""

    critique, cost = call_model(critique_prompt, "gpt")
    total_cost += cost

    # Revise
    revise_prompt = f"""Revise your response based on the critique.

Original question: {question}
Original response: {response}
Critique: {critique}

Provide an improved response that addresses the concerns raised."""

    final, cost = call_model(revise_prompt, "gpt")
    total_cost += cost

    return final, total_cost, {"method": "self_critique", "steps": 3}


def run_fullstack(question: str, q_data: dict) -> tuple[str, float, dict]:
    """
    Full stack verification pipeline:
    1. Enhanced prompt with best learnings
    2. Multi-model generation (3 models)
    3. Each model self-critiques
    4. Verification passes
    5. Informed integration with guidance
    6. Final critique by strongest model
    """
    total_cost = 0.0
    trace = {"steps": []}

    # ========== STEP 1: Enhanced Prompt ==========
    enhanced_prompt = f"""Answer this question thoughtfully.

Guidelines (not prescriptive, just context):
- If you're not certain about a claim, acknowledge your uncertainty level
- If citing sources, only cite ones you're confident exist; otherwise say "I believe" or "based on my understanding"
- You will be evaluated on: accuracy of claims, logical reasoning, and appropriate calibration of confidence
- Being honestly uncertain is valued over false confidence

Question: {question}"""

    log("  Step 1: Generating with enhanced prompt (3 models)...")

    # ========== STEP 2: Multi-model generation ==========
    models = ["gpt", "claude", "gemini"]
    model_responses = {}

    for model in models:
        response, cost = call_model(enhanced_prompt, model)
        total_cost += cost
        model_responses[model] = {"initial": response}
        time.sleep(1)

    trace["steps"].append({"step": "multi_model_generate", "models": list(models)})

    # ========== STEP 3: Self-critique each ==========
    log("  Step 2: Each model self-critiques...")

    for model in models:
        critique_prompt = f"""Review your response and identify potential issues:

Your response: {model_responses[model]['initial'][:2000]}

1. What claims might be wrong or unverifiable?
2. Where are you uncertain?
3. What would a rigorous fact-checker challenge?

Be honest about weaknesses."""

        critique, cost = call_model(critique_prompt, model)
        total_cost += cost
        model_responses[model]["self_critique"] = critique
        time.sleep(1)

    trace["steps"].append({"step": "self_critique"})

    # ========== STEP 4: Verification passes ==========
    log("  Step 3: Verification passes...")

    # Use GPT for claim verification (strong on facts)
    verification_prompt = f"""Verify the claims in this response:

Response: {model_responses['gpt']['initial'][:2000]}
Self-critique: {model_responses['gpt']['self_critique'][:1000]}

For each major factual claim:
- VERIFIED: You're confident this is correct
- UNCERTAIN: Plausible but you can't verify
- SUSPECT: This seems wrong or fabricated

List the claims and their status."""

    claim_verification, cost = call_model(verification_prompt, "gpt")
    total_cost += cost
    trace["steps"].append({"step": "claim_verification"})

    # Use Claude for reasoning verification (strong on nuance)
    reasoning_prompt = f"""Check the logical reasoning in this response:

Response: {model_responses['claude']['initial'][:2000]}

For each inference or conclusion:
1. Does the conclusion follow from the premises?
2. Are there unstated assumptions?
3. Are there logical fallacies?

Be specific about any reasoning issues."""

    reasoning_verification, cost = call_model(reasoning_prompt, "claude")
    total_cost += cost
    trace["steps"].append({"step": "reasoning_verification"})
    time.sleep(1)

    # ========== STEP 5: Informed Integration ==========
    log("  Step 4: Informed integration with guidance...")

    integration_prompt = f"""You are synthesizing responses from three AI models. Your job is to create the best possible answer.

ORIGINAL QUESTION: {question}

MODEL RESPONSES AND SELF-CRITIQUES:

=== GPT-5.2 (strong on factual accuracy, sometimes overconfident) ===
Response: {model_responses['gpt']['initial'][:1500]}
Self-critique: {model_responses['gpt']['self_critique'][:500]}

=== Claude Opus 4.5 (strong on nuance and reasoning, sometimes verbose) ===
Response: {model_responses['claude']['initial'][:1500]}
Self-critique: {model_responses['claude']['self_critique'][:500]}

=== Gemini 2.5 Pro (broad knowledge, sometimes less precise) ===
Response: {model_responses['gemini']['initial'][:1500]}
Self-critique: {model_responses['gemini']['self_critique'][:500]}

VERIFICATION FINDINGS:
Claim verification: {claim_verification[:800]}
Reasoning check: {reasoning_verification[:800]}

INTEGRATION GUIDANCE:
- Where models AGREE: Higher confidence, but still verify it makes sense
- Where models DISAGREE: This is signal! Present the disagreement, don't smooth it over
- Watch for: Confident hallucinations, false consensus, losing uncertainty in synthesis
- Goal: Best answer that preserves appropriate uncertainty

Synthesize the best response, being explicit about confidence levels."""

    integrated, cost = call_model(integration_prompt, "claude", timeout=240)
    total_cost += cost
    trace["steps"].append({"step": "informed_integration"})
    time.sleep(1)

    # ========== STEP 6: Final Critique ==========
    log("  Step 5: Final critique and revision...")

    final_critique_prompt = f"""You are doing a final quality check on this response before it's delivered.

QUESTION: {question}

RESPONSE TO CHECK:
{integrated[:2500]}

EVALUATION CRITERIA (what the response will be judged on):
1. ADVERSARIAL: Would this survive rigorous fact-checking? Are claims verifiable or appropriately hedged?
2. REASONING: Is the logic sound? Do conclusions follow from evidence?
3. CALIBRATION: Is confidence appropriate to the evidence? Does it acknowledge genuine uncertainty?

RED FLAGS to check for:
- Specific statistics without clear sources
- Confident claims about things that are actually uncertain
- False precision (exact numbers when ranges would be more honest)
- Logical leaps or unsupported conclusions

If you find issues, provide a revised response. If it's good, say "APPROVED" and explain why.

Your output should be either:
1. "APPROVED: [reason]" if the response is ready
2. A revised response that fixes the issues you found"""

    final_output, cost = call_model(final_critique_prompt, "claude", timeout=180)
    total_cost += cost
    trace["steps"].append({"step": "final_critique"})

    # If approved, use integrated; otherwise use final revision
    if "APPROVED" in final_output[:100].upper():
        final_response = integrated
        trace["final_action"] = "approved"
    else:
        final_response = final_output
        trace["final_action"] = "revised"

    return final_response, total_cost, {
        "method": "fullstack",
        "steps": 6,
        "trace": trace,
        "model_responses": {k: v["initial"][:500] for k, v in model_responses.items()}
    }


def run_fullstack_lite(question: str, q_data: dict) -> tuple[str, float, dict]:
    """
    Lighter version: Single model with all the prompt learnings + verification.
    For comparison to see if multi-model adds value.
    """
    total_cost = 0.0

    # Enhanced prompt
    enhanced_prompt = f"""Answer this question thoughtfully.

Guidelines:
- If you're not certain about a claim, acknowledge your uncertainty
- Only cite sources you're confident exist
- You will be evaluated on accuracy, reasoning, and calibrated confidence
- Honest uncertainty is valued over false confidence

Question: {question}"""

    response, cost = call_model(enhanced_prompt, "claude")
    total_cost += cost

    # Self-critique
    critique_prompt = f"""Review your response for issues:
Response: {response}
What might be wrong? What would a fact-checker challenge?"""

    critique, cost = call_model(critique_prompt, "claude")
    total_cost += cost

    # Reasoning verification
    verify_prompt = f"""Check the reasoning and claims:
Response: {response}
Critique: {critique}
Mark any claims as VERIFIED/UNCERTAIN/SUSPECT. Check logical validity."""

    verification, cost = call_model(verify_prompt, "claude")
    total_cost += cost

    # Final revision
    revise_prompt = f"""Revise based on critique and verification:
Original: {response}
Critique: {critique}
Verification: {verification}
Provide improved response with appropriate confidence levels."""

    final, cost = call_model(revise_prompt, "claude")
    total_cost += cost

    return final, total_cost, {"method": "fullstack_lite", "steps": 4}


# ============ MAIN EXPERIMENT RUNNER ============

def main():
    log("="*80)
    log("FULL STACK VERIFICATION EXPERIMENT")
    log("Testing comprehensive pipeline on HARD questions")
    log("="*80)

    results = {
        "questions": {},
        "summary": {},
        "total_cost": 0.0
    }

    methods = [
        ("baseline", run_baseline),
        ("anti_fab_only", run_anti_fabrication_only),
        ("self_critique", run_self_critique),
        ("fullstack_lite", lambda q, d: run_fullstack_lite(q, d)),
        ("fullstack", lambda q, d: run_fullstack(q, d)),
    ]

    for q_id, q_data in HARD_QUESTIONS.items():
        log(f"\n{'='*60}")
        log(f"Question: {q_id}")
        log(f"Type: {q_data['type']}")
        log(f"Baseline adversarial: {q_data['baseline_adv']}")
        log(f"{'='*60}")

        results["questions"][q_id] = {
            "question": q_data["question"],
            "type": q_data["type"],
            "baseline_adv": q_data["baseline_adv"],
            "methods": {}
        }

        for method_name, method_fn in methods:
            log(f"\n  Running {method_name}...")

            try:
                if method_name in ["fullstack", "fullstack_lite"]:
                    response, cost, meta = method_fn(q_data["question"], q_data)
                else:
                    response, cost, meta = method_fn(q_data["question"])

                results["total_cost"] += cost

                # Judge the response
                log(f"  Judging {method_name}...")
                scores, judge_cost = run_judge(q_data["question"], response, q_data["type"])
                results["total_cost"] += judge_cost

                results["questions"][q_id]["methods"][method_name] = {
                    "response": response[:2000],
                    "cost": cost,
                    "scores": scores,
                    "meta": {k: v for k, v in meta.items() if k != "trace"}
                }

                s = scores.get('style', '?')
                a = scores.get('adversarial', '?')
                r = scores.get('reasoning', '?')
                log(f"  → S:{s} A:{a} R:{r}")

                if scores.get('justification'):
                    log(f"    {scores['justification'][:100]}...")

            except Exception as e:
                log(f"  ERROR in {method_name}: {e}", "ERROR")
                results["questions"][q_id]["methods"][method_name] = {"error": str(e)}

            time.sleep(2)

    # Summary
    log("\n" + "="*80)
    log("RESULTS SUMMARY")
    log("="*80)

    # Aggregate by method
    method_scores = {}
    for q_id, q_data in results["questions"].items():
        for method, m_data in q_data["methods"].items():
            if "scores" not in m_data:
                continue
            if method not in method_scores:
                method_scores[method] = {"style": [], "adversarial": [], "reasoning": []}
            for metric in ["style", "adversarial", "reasoning"]:
                if m_data["scores"].get(metric) is not None:
                    method_scores[method][metric].append(m_data["scores"][metric])

    log(f"\n{'Method':<20} | Style | Adv  | Rsn  | Avg  | N")
    log("-"*60)

    for method in ["baseline", "anti_fab_only", "self_critique", "fullstack_lite", "fullstack"]:
        if method not in method_scores:
            continue
        scores = method_scores[method]
        n = len(scores["style"])
        if n == 0:
            continue
        avg_s = sum(scores["style"])/n
        avg_a = sum(scores["adversarial"])/n
        avg_r = sum(scores["reasoning"])/n
        avg_all = (avg_s + avg_a + avg_r) / 3
        log(f"{method:<20} | {avg_s:4.1f} | {avg_a:4.1f} | {avg_r:4.1f} | {avg_all:4.1f} | {n}")

    results["summary"] = method_scores

    log(f"\nTotal cost: ${results['total_cost']:.4f}")

    with open(RESULTS_FILE, "w") as f:
        json.dump(results, f, indent=2)
    log(f"Results saved to {RESULTS_FILE}")


if __name__ == "__main__":
    main()

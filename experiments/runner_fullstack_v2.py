#!/usr/bin/env python3
"""
Full Stack Verification v2 - Fixed Pipeline

Changes from v1:
1. Final critique step now explicitly asks for the final answer, not evaluation
2. Better handling of the integration step
3. Removed "APPROVED" option that caused format issues
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
LOG_FILE = EXPERIMENTS_DIR / "experiment_fullstack_v2.log"
RESULTS_FILE = EXPERIMENTS_DIR / "experiment_results_fullstack_v2.json"

# Hard questions where baseline fails
HARD_QUESTIONS = {
    "factual_fabrication": {
        "question": "What percentage of Fortune 500 CEOs have Harvard MBAs specifically? Cite your source.",
        "type": "factual",
        "notes": "Models tend to fabricate specific statistics"
    },
    "factual_complex": {
        "question": "What were the key technical causes of the 2024 CrowdStrike outage that affected millions of Windows computers?",
        "type": "factual",
        "notes": "Recent event with specific technical details"
    },
    "contested_nuanced": {
        "question": "Should a 50-person engineering team at a growth-stage startup migrate from a Django monolith to microservices? They're experiencing scaling issues but have limited DevOps expertise.",
        "type": "contested",
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
- Meta-commentary about evaluation rather than actual answers

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

    just_match = re.search(r'JUSTIFICATION:\s*(.+)', result, re.DOTALL)
    scores['justification'] = just_match.group(1).strip()[:500] if just_match else ""

    return scores, cost


# ============ ENHANCED PROMPT (combining best learnings) ============

ENHANCED_PROMPT_PREFIX = """Answer this question thoughtfully.

Context for your response:
- If you're not certain about a claim, acknowledge your uncertainty level
- If citing sources, only cite ones you're confident exist; otherwise say "I believe" or "based on my understanding"
- You will be evaluated on: (1) accuracy of verifiable claims, (2) logical reasoning, (3) appropriate calibration of confidence
- Being honestly uncertain is valued over false confidence - it's better to say "I don't know the exact figure" than to fabricate one

Question: """


def run_baseline(question: str) -> tuple[str, float, dict]:
    """Plain single model, no enhancements."""
    response, cost = call_model(question, "gpt")
    return response, cost, {"method": "baseline", "steps": 1}


def run_enhanced_single(question: str) -> tuple[str, float, dict]:
    """Single model with enhanced prompt."""
    prompt = ENHANCED_PROMPT_PREFIX + question
    response, cost = call_model(prompt, "claude")
    return response, cost, {"method": "enhanced_single", "steps": 1}


def run_enhanced_critique(question: str) -> tuple[str, float, dict]:
    """Enhanced prompt + self-critique cycle."""
    total_cost = 0.0

    # Generate with enhanced prompt
    prompt = ENHANCED_PROMPT_PREFIX + question
    response, cost = call_model(prompt, "claude")
    total_cost += cost

    # Self-critique
    critique_prompt = f"""Review this response for issues:

Response: {response}

Check for:
1. Any claims that might be fabricated or unverifiable
2. Overconfident language where uncertainty would be more appropriate
3. Logical gaps or unsupported conclusions
4. Missing important caveats or context

What would a rigorous fact-checker challenge?"""

    critique, cost = call_model(critique_prompt, "claude")
    total_cost += cost

    # Revise
    revise_prompt = f"""Revise your response based on the critique.

Original question: {question}
Original response: {response}
Critique: {critique}

Provide an improved response that addresses the concerns. Keep the same format but fix any issues identified."""

    final, cost = call_model(revise_prompt, "claude")
    total_cost += cost

    return final, total_cost, {"method": "enhanced_critique", "steps": 3}


def run_fullstack_v2(question: str, q_data: dict) -> tuple[str, float, dict]:
    """
    Full stack v2 - fixed pipeline:
    1. Enhanced prompt with best learnings
    2. Multi-model generation (3 models)
    3. Each model self-critiques
    4. Informed integration with clear guidance
    5. Final polish pass (not evaluation)
    """
    total_cost = 0.0

    log("  Step 1: Multi-model generation with enhanced prompt...")

    # Step 1-2: Generate with enhanced prompt from 3 models
    models = ["gpt", "claude", "gemini"]
    model_responses = {}

    prompt = ENHANCED_PROMPT_PREFIX + question

    for model in models:
        response, cost = call_model(prompt, model)
        total_cost += cost
        model_responses[model] = {"initial": response}
        time.sleep(1)

    # Step 3: Each model self-critiques
    log("  Step 2: Self-critique pass...")

    for model in models:
        critique_prompt = f"""Briefly review your response for potential issues:

Your response: {model_responses[model]['initial'][:2000]}

List any:
- Claims you're uncertain about
- Potential factual errors
- Areas where you might be overconfident

Be concise - just the key concerns."""

        critique, cost = call_model(critique_prompt, model)
        total_cost += cost
        model_responses[model]["critique"] = critique
        time.sleep(1)

    # Step 4: Informed integration
    log("  Step 3: Informed integration...")

    integration_prompt = f"""Synthesize the best answer from three AI models' responses.

QUESTION: {question}

=== GPT-5.2 ===
Response: {model_responses['gpt']['initial'][:1500]}
Self-identified concerns: {model_responses['gpt']['critique'][:400]}

=== Claude Opus 4.5 ===
Response: {model_responses['claude']['initial'][:1500]}
Self-identified concerns: {model_responses['claude']['critique'][:400]}

=== Gemini 3 Pro ===
Response: {model_responses['gemini']['initial'][:1500]}
Self-identified concerns: {model_responses['gemini']['critique'][:400]}

INTEGRATION GUIDANCE:
- Where models AGREE: Higher confidence, but verify it makes sense
- Where models DISAGREE: This is valuable signal - preserve the disagreement, don't smooth it over
- Each model flagged their own concerns - weight those appropriately
- Claude tends to be strong on nuance, GPT on facts, Gemini on breadth

Create the BEST POSSIBLE ANSWER to the original question. Output ONLY the answer, no meta-commentary."""

    integrated, cost = call_model(integration_prompt, "claude", timeout=240)
    total_cost += cost
    time.sleep(1)

    # Step 5: Final polish (NOT evaluation - just polish)
    log("  Step 4: Final polish...")

    polish_prompt = f"""Polish this response for final delivery.

Question: {question}

Draft response:
{integrated[:2500]}

Your job:
1. Check that confidence levels match the evidence provided
2. Ensure any hedging language is clear and not weaselly
3. Make sure the response directly answers the question
4. Clean up any awkward phrasing

Output the FINAL POLISHED RESPONSE only. Do not add evaluation commentary or meta-discussion."""

    final, cost = call_model(polish_prompt, "claude", timeout=180)
    total_cost += cost

    return final, total_cost, {
        "method": "fullstack_v2",
        "steps": 5,
        "model_count": 3
    }


def run_fullstack_lite_v2(question: str) -> tuple[str, float, dict]:
    """
    Lighter version: Claude with enhanced prompt + verification + polish.
    """
    total_cost = 0.0

    # Generate with enhanced prompt
    prompt = ENHANCED_PROMPT_PREFIX + question
    response, cost = call_model(prompt, "claude")
    total_cost += cost

    # Critique + verification
    critique_prompt = f"""Review this response critically:

Question: {question}
Response: {response}

Check:
1. Are any claims fabricated or unverifiable?
2. Is confidence appropriately calibrated?
3. Are there logical gaps?
4. What would a fact-checker challenge?

Provide specific critique."""

    critique, cost = call_model(critique_prompt, "claude")
    total_cost += cost

    # Reasoning verification
    verify_prompt = f"""Check the logical reasoning:

Response: {response[:1500]}
Critique: {critique[:800]}

For each key claim or inference:
- Does it follow logically?
- Is there sufficient evidence?
- Are there unstated assumptions?

List any reasoning issues found."""

    verification, cost = call_model(verify_prompt, "claude")
    total_cost += cost

    # Final revision
    revise_prompt = f"""Create the final response incorporating all feedback.

Original question: {question}
Original response: {response}
Critique: {critique}
Reasoning check: {verification}

Provide the IMPROVED FINAL RESPONSE that addresses all issues. Output only the response, no meta-commentary."""

    final, cost = call_model(revise_prompt, "claude")
    total_cost += cost

    return final, total_cost, {"method": "fullstack_lite_v2", "steps": 4}


# ============ MAIN ============

def main():
    log("="*80)
    log("FULL STACK VERIFICATION v2")
    log("Fixed pipeline - testing on hard questions")
    log("="*80)

    results = {
        "questions": {},
        "summary": {},
        "total_cost": 0.0
    }

    methods = [
        ("baseline", run_baseline),
        ("enhanced_single", run_enhanced_single),
        ("enhanced_critique", run_enhanced_critique),
        ("fullstack_lite_v2", lambda q, d=None: run_fullstack_lite_v2(q)),
        ("fullstack_v2", lambda q, d: run_fullstack_v2(q, d)),
    ]

    for q_id, q_data in HARD_QUESTIONS.items():
        log(f"\n{'='*60}")
        log(f"Question: {q_id}")
        log(f"Type: {q_data['type']}")
        log(f"{'='*60}")

        results["questions"][q_id] = {
            "question": q_data["question"],
            "type": q_data["type"],
            "methods": {}
        }

        for method_name, method_fn in methods:
            log(f"\n  Running {method_name}...")

            try:
                if method_name == "fullstack_v2":
                    response, cost, meta = method_fn(q_data["question"], q_data)
                else:
                    response, cost, meta = method_fn(q_data["question"])

                results["total_cost"] += cost

                # Judge
                log(f"  Judging {method_name}...")
                scores, judge_cost = run_judge(q_data["question"], response, q_data["type"])
                results["total_cost"] += judge_cost

                results["questions"][q_id]["methods"][method_name] = {
                    "response": response[:2000],
                    "cost": cost,
                    "scores": scores,
                    "meta": meta
                }

                s = scores.get('style', '?')
                a = scores.get('adversarial', '?')
                r = scores.get('reasoning', '?')
                avg = (s + a + r) / 3 if all(isinstance(x, int) for x in [s,a,r]) else '?'
                log(f"  → S:{s} A:{a} R:{r} (avg:{avg:.1f})" if avg != '?' else f"  → S:{s} A:{a} R:{r}")

            except Exception as e:
                log(f"  ERROR: {e}", "ERROR")
                results["questions"][q_id]["methods"][method_name] = {"error": str(e)}

            time.sleep(2)

    # Summary
    log("\n" + "="*80)
    log("RESULTS SUMMARY")
    log("="*80)

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

    for method in ["baseline", "enhanced_single", "enhanced_critique", "fullstack_lite_v2", "fullstack_v2"]:
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

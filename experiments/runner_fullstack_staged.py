#!/usr/bin/env python3
"""
Full Stack Verification with Per-Stage Evaluation

Evaluates each stage of the pipeline to understand where value is created:
1. Each individual model response
2. After self-critique
3. After integration
4. Final output

This helps us understand:
- Which models contribute most value
- Does self-critique help or hurt?
- Does integration improve or destroy value?
"""

import json
import os
import re
import subprocess
import time
from datetime import datetime
from pathlib import Path

EXPERIMENTS_DIR = Path(__file__).parent
LOG_FILE = EXPERIMENTS_DIR / "experiment_staged.log"
RESULTS_FILE = EXPERIMENTS_DIR / "experiment_results_staged.json"

HARD_QUESTIONS = {
    "factual_fabrication": {
        "question": "What percentage of Fortune 500 CEOs have Harvard MBAs specifically? Cite your source.",
        "type": "factual",
    },
    "factual_complex": {
        "question": "What were the key technical causes of the 2024 CrowdStrike outage that affected millions of Windows computers?",
        "type": "factual",
    },
}

ENHANCED_PROMPT_PREFIX = """Answer this question thoughtfully.

Context:
- If uncertain about a claim, acknowledge it
- Only cite sources you're confident exist
- Honest uncertainty is valued over false confidence

Question: """


def log(message: str, level: str = "INFO"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] [{level}] {message}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")


def call_model(prompt: str, model: str = "gpt", timeout: int = 180) -> tuple[str, float]:
    cmd = ["minds", "ask", "--model", model, "--yes", prompt]
    for attempt in range(3):
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            output = result.stdout.strip()
            if output:
                return output, 0.0
            time.sleep(3)
        except:
            time.sleep(3)
    return "", 0.0


def run_judge(question: str, response: str, q_type: str) -> dict:
    """Quick judge - returns scores dict."""
    prompt = f"""Evaluate (0-10 each):

Question: {question}
Response: {response[:2500]}

STYLE_SCORE: [0-10] (depth, clarity)
ADVERSARIAL_SCORE: [0-10] (fact-checkable, calibrated confidence)
REASONING_SCORE: [0-10] (logical structure)

Output scores only, one per line."""

    result, _ = call_model(prompt, "claude", timeout=60)

    scores = {}
    for metric in ["STYLE", "ADVERSARIAL", "REASONING"]:
        match = re.search(rf'{metric}_SCORE:\s*(\d+)', result)
        scores[metric.lower()] = int(match.group(1)) if match else None

    return scores


def run_staged_pipeline(question: str, q_type: str) -> dict:
    """Run pipeline with evaluation at each stage."""
    results = {
        "stages": {},
        "progression": []
    }

    log("  Stage 1: Individual model responses...")

    # Stage 1: Individual models with enhanced prompt
    prompt = ENHANCED_PROMPT_PREFIX + question
    models = ["gpt", "claude", "gemini"]
    model_responses = {}

    for model in models:
        response, _ = call_model(prompt, model)
        model_responses[model] = response

        # Evaluate each model individually
        scores = run_judge(question, response, q_type)
        avg = sum(v for v in scores.values() if v) / 3 if all(scores.values()) else 0

        results["stages"][f"1_{model}_initial"] = {
            "response": response[:1000],
            "scores": scores,
            "avg": round(avg, 1)
        }
        log(f"    {model}: S:{scores.get('style','?')} A:{scores.get('adversarial','?')} R:{scores.get('reasoning','?')} (avg:{avg:.1f})")
        time.sleep(1)

    # Stage 2: Self-critique for best model (Claude)
    log("  Stage 2: Self-critique (Claude)...")

    critique_prompt = f"""Review your response for issues:
Response: {model_responses['claude']}
What might be wrong? What would a fact-checker challenge?"""

    critique, _ = call_model(critique_prompt, "claude")

    revise_prompt = f"""Revise based on critique:
Original: {model_responses['claude']}
Critique: {critique}
Provide improved response."""

    revised, _ = call_model(revise_prompt, "claude")
    scores = run_judge(question, revised, q_type)
    avg = sum(v for v in scores.values() if v) / 3 if all(scores.values()) else 0

    results["stages"]["2_claude_critiqued"] = {
        "response": revised[:1000],
        "scores": scores,
        "avg": round(avg, 1)
    }
    log(f"    After critique: S:{scores.get('style','?')} A:{scores.get('adversarial','?')} R:{scores.get('reasoning','?')} (avg:{avg:.1f})")

    # Stage 3: Integration of all 3 models
    log("  Stage 3: Multi-model integration...")

    integration_prompt = f"""Synthesize the best answer from three models:

Question: {question}

GPT: {model_responses['gpt'][:1200]}
Claude: {model_responses['claude'][:1200]}
Gemini: {model_responses['gemini'][:1200]}

Where models disagree, preserve the disagreement. Create the best answer."""

    integrated, _ = call_model(integration_prompt, "claude", timeout=180)
    scores = run_judge(question, integrated, q_type)
    avg = sum(v for v in scores.values() if v) / 3 if all(scores.values()) else 0

    results["stages"]["3_integrated"] = {
        "response": integrated[:1000],
        "scores": scores,
        "avg": round(avg, 1)
    }
    log(f"    Integrated: S:{scores.get('style','?')} A:{scores.get('adversarial','?')} R:{scores.get('reasoning','?')} (avg:{avg:.1f})")

    # Stage 4: Final polish
    log("  Stage 4: Final polish...")

    polish_prompt = f"""Polish this response:
{integrated[:2000]}

Ensure confidence matches evidence. Output final response only."""

    final, _ = call_model(polish_prompt, "claude")
    scores = run_judge(question, final, q_type)
    avg = sum(v for v in scores.values() if v) / 3 if all(scores.values()) else 0

    results["stages"]["4_final"] = {
        "response": final[:1000],
        "scores": scores,
        "avg": round(avg, 1)
    }
    log(f"    Final: S:{scores.get('style','?')} A:{scores.get('adversarial','?')} R:{scores.get('reasoning','?')} (avg:{avg:.1f})")

    # Build progression summary
    for stage_name in sorted(results["stages"].keys()):
        stage = results["stages"][stage_name]
        results["progression"].append({
            "stage": stage_name,
            "avg": stage["avg"],
            "adv": stage["scores"].get("adversarial", 0)
        })

    return results


def main():
    log("="*70)
    log("STAGED PIPELINE EVALUATION")
    log("="*70)

    all_results = {}

    for q_id, q_data in HARD_QUESTIONS.items():
        log(f"\n{'='*60}")
        log(f"Question: {q_id}")
        log(f"{'='*60}")

        results = run_staged_pipeline(q_data["question"], q_data["type"])
        all_results[q_id] = results

        # Show progression
        log(f"\n  Progression for {q_id}:")
        for p in results["progression"]:
            log(f"    {p['stage']}: avg={p['avg']}, adv={p['adv']}")

    # Summary
    log("\n" + "="*70)
    log("VALUE CREATION ANALYSIS")
    log("="*70)

    for q_id, results in all_results.items():
        log(f"\n{q_id}:")
        prog = results["progression"]

        # Find best individual model
        individual = [p for p in prog if p["stage"].startswith("1_")]
        best_individual = max(individual, key=lambda x: x["avg"])

        # Get critique and integration scores
        critiqued = next((p for p in prog if "critiqued" in p["stage"]), None)
        integrated = next((p for p in prog if "integrated" in p["stage"]), None)
        final = next((p for p in prog if "final" in p["stage"]), None)

        log(f"  Best individual: {best_individual['stage']} (avg={best_individual['avg']}, adv={best_individual['adv']})")
        if critiqued:
            delta = critiqued['avg'] - best_individual['avg']
            log(f"  After critique: avg={critiqued['avg']} (Δ={delta:+.1f})")
        if integrated:
            delta = integrated['avg'] - best_individual['avg']
            log(f"  After integration: avg={integrated['avg']} (Δ={delta:+.1f})")
        if final:
            delta = final['avg'] - best_individual['avg']
            log(f"  Final: avg={final['avg']} (Δ={delta:+.1f})")

    with open(RESULTS_FILE, "w") as f:
        json.dump(all_results, f, indent=2)
    log(f"\nResults saved to {RESULTS_FILE}")


if __name__ == "__main__":
    main()

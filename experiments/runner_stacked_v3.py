#!/usr/bin/env python3
"""
Stacked verification pipeline v3 - incorporating synthesis research findings.

Based on Issue #8 experiments showing:
- Naive synthesis destroys value when models disagree
- Cross-verification synthesis preserves value
- Single model + verification often beats multi-model synthesis

This script tests multiple stacked approaches:
A. Single Model + Verification (accuracy focus)
B. Multi-Model + Cross-Verification (best of both worlds)
C. Pick-Best + Polish (avoids synthesis entirely)
"""

import json
import subprocess
import logging
from datetime import datetime
from typing import Optional

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(message)s',
    datefmt='%H:%M:%S'
)
log = logging.getLogger(__name__)

# Test questions covering different types
QUESTIONS = {
    "factual_fabrication": {
        "question": "What percentage of Fortune 500 CEOs have Harvard MBAs specifically? Cite your source.",
        "type": "unverifiable_with_fabrication_risk",
        "notes": "Tests whether synthesis launders fabricated statistics"
    },
    "factual_verifiable": {
        "question": "What were the key technical causes of the 2024 CrowdStrike outage?",
        "type": "factual_verifiable",
        "notes": "Models should agree on documented facts"
    },
    "contested_nuanced": {
        "question": "When should you use microservices vs monolith architecture?",
        "type": "contested_opinion",
        "notes": "Legitimate disagreement, should present both sides"
    }
}

# Enhanced prompt based on research
ENHANCED_PROMPT = """Answer this question thoughtfully.

Context:
- If you're uncertain about a claim, acknowledge your uncertainty level
- Only cite sources you're confident exist
- You will be evaluated on accuracy, reasoning, and appropriate confidence calibration
- Being honestly uncertain is valued over false confidence

Question: """

# Cross-verification synthesis prompt (from research)
CROSS_VERIFICATION_SYNTHESIS = """You are synthesizing responses from multiple AI models.

RULES:
1. INCLUDE claims corroborated by 2+ models (state with confidence)
2. INCLUDE consensus uncertainty (if all models say they can't verify, preserve this)
3. EXCLUDE specific numbers, sources, or citations that only ONE model provides
   - If other models explicitly say they can't verify such claims, this signals fabrication
4. For contested topics, present both sides fairly
5. Natural style, be direct about what's known vs uncertain

Model responses:
{responses}

Question: {question}

Synthesize using only verified/corroborated information:"""

# Pick-best prompt
PICK_BEST_PROMPT = """You are selecting the BEST response from multiple AI models.

Evaluate each response on:
1. Epistemic honesty (doesn't fabricate, acknowledges uncertainty appropriately)
2. Accuracy (claims are verifiable or appropriately hedged)
3. Helpfulness (provides actionable guidance)

If one response provides specific statistics that others can't verify, prefer the responses that acknowledge uncertainty.

Model responses:
{responses}

Question: {question}

Select and output the best response (you may lightly edit for clarity):"""

# Self-critique prompt
SELF_CRITIQUE_PROMPT = """Review your previous response for potential issues:

1. Are there any claims that might be fabricated or hard to verify?
2. Are citations real and accurate?
3. Is the confidence level appropriate?
4. Could any statements be challenged by a fact-checker?

Previous response:
{response}

If you find issues, provide a corrected response. If it's solid, output it unchanged with brief confirmation of why it's sound."""

# Reasoning verification prompt
REASONING_VERIFICATION_PROMPT = """Verify the reasoning in this response:

1. Are conclusions supported by the evidence presented?
2. Are there logical gaps or unsupported leaps?
3. Are alternative explanations considered where appropriate?

Response to verify:
{response}

If reasoning is sound, confirm briefly. If there are issues, provide corrections."""


def query_model(prompt: str, model: str = "claude") -> str:
    """Query a single model."""
    cmd = ["minds", "ask", "--model", model, "-y", prompt]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    return result.stdout.strip()


def query_multi(prompt: str) -> dict[str, str]:
    """Query multiple models in parallel."""
    cmd = ["minds", "ask", "-y", "--verbose", prompt]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    # Parse individual responses from verbose output
    # For now, return the full output
    return {"combined": result.stdout.strip()}


def extract_response_text(output: str) -> str:
    """Extract just the response text from minds CLI output."""
    import re
    # Remove the box drawing characters and timing info
    lines = output.split('\n')
    content_lines = []
    in_box = False
    for line in lines:
        if '─' in line and ('╭' in line or '╰' in line):
            in_box = not in_box if '╭' in line else not in_box
            continue
        if in_box or (line.strip() and not line.startswith('�') and 'ms)' not in line):
            # Remove box side characters
            cleaned = re.sub(r'^[│\s]+', '', line)
            cleaned = re.sub(r'[│\s]+$', '', cleaned)
            if cleaned:
                content_lines.append(cleaned)
    return '\n'.join(content_lines)


def judge_response(response: str, question: str) -> dict:
    """Judge response quality."""
    prompt = f"""Rate this response 0-10 on each dimension.

Question: {question}

Response:
{response}

STYLE (0-10): Clarity, natural flow, appropriate length
ADVERSARIAL (0-10): Would survive fact-checking? No fabrication? Honest about uncertainty?
REASONING (0-10): Clear logic? Conclusions well-supported? Decisive where appropriate?

Output JSON only: {{"style": N, "adversarial": N, "reasoning": N}}"""

    result = query_model(prompt, "claude")

    import re
    try:
        match = re.search(r'\{[^{}]*"style"[^{}]*\}', result, re.DOTALL)
        if match:
            return json.loads(re.sub(r'\s+', ' ', match.group()))
    except:
        pass
    return {"style": 5, "adversarial": 5, "reasoning": 5}


def approach_a_single_verification(question: str) -> dict:
    """Approach A: Single strong model + verification passes."""
    log.info("  Approach A: Single Model + Verification")

    # Step 1: Enhanced prompt + single model
    prompt = ENHANCED_PROMPT + question
    response = query_model(prompt, "claude")
    response = extract_response_text(response)

    # Step 2: Self-critique
    critique_prompt = SELF_CRITIQUE_PROMPT.format(response=response)
    critiqued = query_model(critique_prompt, "claude")
    critiqued = extract_response_text(critiqued)

    # Step 3: Reasoning verification
    verify_prompt = REASONING_VERIFICATION_PROMPT.format(response=critiqued)
    final = query_model(verify_prompt, "claude")
    final = extract_response_text(final)

    return {"response": final, "method": "single_verification"}


def approach_b_cross_verification(question: str) -> dict:
    """Approach B: Multi-model + cross-verification synthesis."""
    log.info("  Approach B: Multi-Model + Cross-Verification")

    # Step 1: Query multiple models
    prompt = ENHANCED_PROMPT + question
    multi_result = query_multi(prompt)

    # Step 2: Cross-verification synthesis
    synth_prompt = CROSS_VERIFICATION_SYNTHESIS.format(
        responses=multi_result["combined"],
        question=question
    )
    synthesis = query_model(synth_prompt, "claude")
    synthesis = extract_response_text(synthesis)

    return {"response": synthesis, "method": "cross_verification"}


def approach_c_pick_best(question: str) -> dict:
    """Approach C: Multi-model + pick best response."""
    log.info("  Approach C: Pick Best")

    # Step 1: Query multiple models
    prompt = ENHANCED_PROMPT + question
    multi_result = query_multi(prompt)

    # Step 2: Pick best
    pick_prompt = PICK_BEST_PROMPT.format(
        responses=multi_result["combined"],
        question=question
    )
    best = query_model(pick_prompt, "claude")
    best = extract_response_text(best)

    return {"response": best, "method": "pick_best"}


def approach_baseline(question: str) -> dict:
    """Baseline: Just ask the question directly."""
    log.info("  Baseline: Direct query")

    response = query_model(question, "claude")
    response = extract_response_text(response)

    return {"response": response, "method": "baseline"}


def run_experiment():
    """Run all approaches on all questions."""
    results = {
        "timestamp": datetime.now().isoformat(),
        "questions": {}
    }

    approaches = [
        ("baseline", approach_baseline),
        ("single_verification", approach_a_single_verification),
        ("cross_verification", approach_b_cross_verification),
        ("pick_best", approach_c_pick_best),
    ]

    for q_name, q_data in QUESTIONS.items():
        log.info(f"\n{'='*60}")
        log.info(f"Question: {q_name}")
        log.info(f"Type: {q_data['type']}")
        log.info(f"{'='*60}")

        question = q_data["question"]
        results["questions"][q_name] = {
            "question": question,
            "type": q_data["type"],
            "approaches": {}
        }

        for approach_name, approach_fn in approaches:
            try:
                log.info(f"\nRunning {approach_name}...")
                result = approach_fn(question)

                # Judge the response
                scores = judge_response(result["response"], question)
                avg = (scores["style"] + scores["adversarial"] + scores["reasoning"]) / 3

                log.info(f"  Scores: S:{scores['style']} A:{scores['adversarial']} R:{scores['reasoning']} (avg:{avg:.1f})")

                results["questions"][q_name]["approaches"][approach_name] = {
                    "response": result["response"][:500] + "..." if len(result["response"]) > 500 else result["response"],
                    "scores": scores,
                    "avg": avg
                }

            except Exception as e:
                log.error(f"  Error: {e}")
                results["questions"][q_name]["approaches"][approach_name] = {"error": str(e)}

    # Summary
    log.info(f"\n{'='*60}")
    log.info("SUMMARY")
    log.info(f"{'='*60}")

    for q_name, q_data in results["questions"].items():
        log.info(f"\n{q_name}:")
        for approach_name, approach_data in q_data["approaches"].items():
            if "scores" in approach_data:
                s = approach_data["scores"]
                log.info(f"  {approach_name}: S:{s['style']} A:{s['adversarial']} R:{s['reasoning']} (avg:{approach_data['avg']:.1f})")

    # Save results
    output_file = "/home/keeva/socrates/experiments/experiment_results_stacked_v3.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    log.info(f"\nResults saved to {output_file}")

    return results


if __name__ == "__main__":
    run_experiment()

#!/usr/bin/env python3
"""
Fullstack Verification Pipeline v3 - Refined based on synthesis research.

Original request:
1. Best prompt learnings (anti-fabrication, cite sources)
2. Tell model what it will be evaluated on (not prescriptive)
3. Self critique + verification + reasoning verification passes
4. Integrate answers with guidance about model strengths and what to look out for
5. Final critique by strongest model

Updated with research findings:
- Integration uses cross-verification (only include corroborated claims)
- Don't repeat unverified specifics from single models
- Preserve honest uncertainty
- Final critique focuses on verification, not content changes

Supports testing with 3 vs 5 models to compare synthesis quality.
"""

import json
import subprocess
import logging
import re
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(message)s',
    datefmt='%H:%M:%S'
)
log = logging.getLogger(__name__)

# Test questions
QUESTIONS = {
    "factual_fabrication": "What percentage of Fortune 500 CEOs have Harvard MBAs specifically? Cite your source.",
    "factual_verifiable": "What were the key technical causes of the 2024 CrowdStrike outage?",
    "contested_nuanced": "When should you use microservices vs monolith architecture?",
}

# =============================================================================
# STEP 1: Enhanced Prompt (anti-fabrication + evaluation context)
# =============================================================================
ENHANCED_PROMPT = """Answer this question thoughtfully.

CONTEXT FOR YOUR RESPONSE:
- Your response will be evaluated on: accuracy of claims, logical reasoning, and appropriate confidence calibration
- If you're uncertain about a specific fact, acknowledge the uncertainty rather than guessing
- Only cite sources you're confident exist - it's better to say "based on my understanding" than to fabricate a citation
- Being honestly uncertain is valued over false confidence

QUESTION: {question}"""

# =============================================================================
# STEP 2: Self-Critique Pass
# =============================================================================
SELF_CRITIQUE_PROMPT = """Review your previous response critically.

CHECK FOR:
1. Any claims that might be fabricated or unverifiable
2. Citations or sources that may not exist
3. Overconfident language where uncertainty would be more appropriate
4. Logical gaps or unsupported conclusions

YOUR PREVIOUS RESPONSE:
{response}

If you find issues, provide a CORRECTED response.
If it's solid, output it with a brief note confirming why it's sound.
Focus on substance, not just adding hedges."""

# =============================================================================
# STEP 3: Reasoning Verification Pass
# =============================================================================
REASONING_VERIFICATION_PROMPT = """Verify the reasoning quality in this response.

CHECK:
1. Are conclusions actually supported by the evidence given?
2. Are there logical leaps or gaps?
3. Are alternative explanations considered where appropriate?
4. Is the confidence level calibrated to the evidence?

RESPONSE TO VERIFY:
{response}

If reasoning is sound, confirm briefly and output the response.
If there are issues, fix them and explain what you changed."""

# =============================================================================
# STEP 4: Cross-Verification Integration (KEY IMPROVEMENT)
# =============================================================================
CROSS_VERIFICATION_INTEGRATION_PROMPT = """You are integrating responses from multiple AI models into one authoritative answer.

CRITICAL RULES (based on research findings):

1. CORROBORATION REQUIRED FOR SPECIFICS:
   - Only include specific numbers, statistics, or source citations if 2+ models agree
   - If one model cites a specific source but others say they can't verify, EXCLUDE it
   - This prevents "laundering" fabricated claims through synthesis

2. PRESERVE HONEST UNCERTAINTY:
   - If models agree they can't verify something, preserve that uncertainty
   - Don't resolve uncertainty by picking the most confident-sounding answer

3. MODEL STRENGTH GUIDANCE:
   - Claude and GPT tend to be more epistemically cautious
   - If they refuse to provide a specific figure but another model does, trust the caution
   - Confident-sounding specifics from a single model are a fabrication red flag

4. FOR CONTESTED TOPICS:
   - When models genuinely disagree on approach/opinion, present both sides fairly
   - This is different from factual claims where disagreement signals fabrication

INTEGRATION APPROACH:
- Lead with what IS corroborated across models
- Be direct about what couldn't be verified
- Provide actionable guidance (where to find verified info)
- Natural style, not rigid structure

MODEL RESPONSES:
{responses}

ORIGINAL QUESTION: {question}

Create the integrated response following these rules:"""

# =============================================================================
# STEP 5: Final Verification (by strongest model)
# =============================================================================
FINAL_VERIFICATION_PROMPT = """You are performing final verification on this integrated response.

YOUR ROLE: Verify quality, don't rewrite content.

CHECK:
1. Does it avoid presenting unverified claims as fact?
2. Is uncertainty appropriately signaled?
3. Is the reasoning sound and conclusions well-supported?
4. Is it helpful and actionable?

RESPONSE TO VERIFY:
{response}

ORIGINAL QUESTION: {question}

If the response passes verification, output it with minimal changes (formatting only).
If there are substantive issues, fix them and note what you changed.

OUTPUT THE FINAL RESPONSE:"""


def query_model(prompt: str, model: str = "claude") -> str:
    """Query a single model."""
    cmd = ["minds", "ask", "--model", model, "-y", prompt]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    return result.stdout.strip()


def query_multi_models(prompt: str, models: list[str] = None) -> dict[str, str]:
    """Query multiple models and return individual responses."""
    if models is None:
        models = ["claude", "gpt", "gemini"]

    responses = {}
    for model in models:
        log.info(f"    Querying {model}...")
        response = query_model(prompt, model)
        responses[model] = extract_response_text(response)

    return responses


def extract_response_text(output: str) -> str:
    """Extract response text from minds CLI output."""
    lines = output.split('\n')
    content_lines = []
    in_box = False

    for line in lines:
        if '─' in line and ('╭' in line or '╰' in line):
            in_box = '╭' in line
            continue
        if in_box:
            cleaned = re.sub(r'^[│\s]+', '', line)
            cleaned = re.sub(r'[│\s]+$', '', cleaned)
            if cleaned:
                content_lines.append(cleaned)

    return '\n'.join(content_lines) if content_lines else output


def judge_response(response: str, question: str) -> dict:
    """Judge response quality with multi-model panel."""
    prompt = f"""Rate this response 0-10 on each dimension. Be critical.

Question: {question}

Response:
{response}

STYLE (0-10): Natural flow, clarity, appropriate length
ADVERSARIAL (0-10): Would survive fact-checking? No fabrication? Honest about uncertainty?
REASONING (0-10): Clear logic? Conclusions well-supported? Decisive where appropriate?

Output JSON only: {{"style": N, "adversarial": N, "reasoning": N}}"""

    result = query_model(prompt, "claude")

    try:
        match = re.search(r'\{[^{}]*"style"[^{}]*\}', result, re.DOTALL)
        if match:
            return json.loads(re.sub(r'\s+', ' ', match.group()))
    except:
        pass
    return {"style": 5, "adversarial": 5, "reasoning": 5}


def run_fullstack_pipeline(question: str, models: list[str] = None) -> dict:
    """Run the complete fullstack verification pipeline.

    Args:
        question: The question to answer
        models: List of models to query. Default is 3 models: ["claude", "gpt", "gemini"]
                Can also use 5 models: ["claude", "gpt", "gemini", "grok", "deepseek"]
    """
    if models is None:
        models = ["claude", "gpt", "gemini"]

    stages = {}
    stages["model_count"] = len(models)

    # STEP 1: Enhanced prompt + multi-model query
    log.info(f"  Step 1: Multi-model query ({len(models)} models) with enhanced prompt")
    enhanced_q = ENHANCED_PROMPT.format(question=question)
    model_responses = query_multi_models(enhanced_q, models)
    stages["1_initial_responses"] = model_responses

    # STEP 2: Self-critique each response
    log.info("  Step 2: Self-critique pass")
    critiqued_responses = {}
    for model, response in model_responses.items():
        critique_prompt = SELF_CRITIQUE_PROMPT.format(response=response)
        critiqued = query_model(critique_prompt, model)
        critiqued_responses[model] = extract_response_text(critiqued)
    stages["2_critiqued_responses"] = critiqued_responses

    # STEP 3: Reasoning verification on Claude's response (strongest)
    log.info("  Step 3: Reasoning verification")
    verify_prompt = REASONING_VERIFICATION_PROMPT.format(response=critiqued_responses["claude"])
    verified_claude = query_model(verify_prompt, "claude")
    verified_claude = extract_response_text(verified_claude)
    stages["3_verified_claude"] = verified_claude

    # STEP 4: Cross-verification integration
    log.info("  Step 4: Cross-verification integration")
    formatted_responses = "\n\n".join([
        f"**{model.upper()}:**\n{response}"
        for model, response in critiqued_responses.items()
    ])
    integration_prompt = CROSS_VERIFICATION_INTEGRATION_PROMPT.format(
        responses=formatted_responses,
        question=question
    )
    integrated = query_model(integration_prompt, "claude")
    integrated = extract_response_text(integrated)
    stages["4_integrated"] = integrated

    # STEP 5: Final verification
    log.info("  Step 5: Final verification")
    final_prompt = FINAL_VERIFICATION_PROMPT.format(
        response=integrated,
        question=question
    )
    final = query_model(final_prompt, "claude")
    final = extract_response_text(final)
    stages["5_final"] = final

    return {
        "stages": stages,
        "final_response": final
    }


def run_baseline(question: str) -> str:
    """Run baseline for comparison."""
    response = query_model(question, "claude")
    return extract_response_text(response)


def run_experiment():
    """Run the fullstack pipeline on all test questions with 3 and 5 models."""
    results = {
        "timestamp": datetime.now().isoformat(),
        "pipeline_version": "fullstack_v3",
        "questions": {}
    }

    # Model configurations to test
    MODEL_CONFIGS = {
        "3_models": ["claude", "gpt", "gemini"],
        "5_models": ["claude", "gpt", "gemini", "grok", "deepseek"],
    }

    for q_name, question in QUESTIONS.items():
        log.info(f"\n{'='*60}")
        log.info(f"Question: {q_name}")
        log.info(f"{'='*60}")

        results["questions"][q_name] = {
            "question": question,
            "configs": {}
        }

        # Run baseline
        log.info("\nRunning baseline...")
        baseline = run_baseline(question)
        baseline_scores = judge_response(baseline, question)
        baseline_avg = sum(baseline_scores.values()) / 3
        log.info(f"  Baseline: S:{baseline_scores['style']} A:{baseline_scores['adversarial']} R:{baseline_scores['reasoning']} (avg:{baseline_avg:.1f})")

        results["questions"][q_name]["baseline"] = {
            "response": baseline[:500] + "..." if len(baseline) > 500 else baseline,
            "scores": baseline_scores,
            "avg": baseline_avg
        }

        # Run fullstack pipeline with each model configuration
        for config_name, models in MODEL_CONFIGS.items():
            log.info(f"\nRunning fullstack pipeline ({config_name})...")
            pipeline_result = run_fullstack_pipeline(question, models)
            final_scores = judge_response(pipeline_result["final_response"], question)
            final_avg = sum(final_scores.values()) / 3
            log.info(f"  {config_name}: S:{final_scores['style']} A:{final_scores['adversarial']} R:{final_scores['reasoning']} (avg:{final_avg:.1f})")

            delta = final_avg - baseline_avg
            log.info(f"  Delta vs baseline: {delta:+.1f}")

            results["questions"][q_name]["configs"][config_name] = {
                "models": models,
                "stages": {k: (v[:300] + "..." if isinstance(v, str) and len(v) > 300 else v)
                          for k, v in pipeline_result["stages"].items()},
                "final_response": pipeline_result["final_response"][:500] + "...",
                "scores": final_scores,
                "avg": final_avg,
                "delta_vs_baseline": delta
            }

    # Summary
    log.info(f"\n{'='*60}")
    log.info("SUMMARY: 3 Models vs 5 Models")
    log.info(f"{'='*60}")

    log.info(f"\n{'Question':<25} | {'Baseline':>8} | {'3 Models':>8} | {'5 Models':>8} | {'Best':>10}")
    log.info("-" * 70)

    for q_name, data in results["questions"].items():
        baseline_avg = data["baseline"]["avg"]
        avg_3 = data["configs"]["3_models"]["avg"]
        avg_5 = data["configs"]["5_models"]["avg"]
        best = "3_models" if avg_3 >= avg_5 else "5_models"
        log.info(f"{q_name:<25} | {baseline_avg:>8.1f} | {avg_3:>8.1f} | {avg_5:>8.1f} | {best:>10}")

    # Overall comparison
    log.info(f"\n{'='*60}")
    log.info("OVERALL AVERAGES")
    log.info(f"{'='*60}")

    all_baseline = [d["baseline"]["avg"] for d in results["questions"].values()]
    all_3 = [d["configs"]["3_models"]["avg"] for d in results["questions"].values()]
    all_5 = [d["configs"]["5_models"]["avg"] for d in results["questions"].values()]

    log.info(f"Baseline:  {sum(all_baseline)/len(all_baseline):.1f}")
    log.info(f"3 Models:  {sum(all_3)/len(all_3):.1f}")
    log.info(f"5 Models:  {sum(all_5)/len(all_5):.1f}")

    # Save
    output_file = "/home/keeva/socrates/experiments/experiment_results_fullstack_v3.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    log.info(f"\nResults saved to {output_file}")

    return results


if __name__ == "__main__":
    run_experiment()

#!/usr/bin/env python3
"""
Comprehensive Verification Experiment - Testing all variations.

This experiment tests a wide range of configurations to understand:
1. Which prompting strategies add value
2. Which pipeline stages add value (per-stage scoring)
3. Whether more models help or hurt
4. Which synthesis methods work best
5. Interaction effects between approaches

Configurations tested:
- Prompt types: baseline, truth-aware, anti-fabrication, combined
- Pipeline stages: none, self-critique, reasoning-verify, full-stack
- Synthesis methods: none, naive, cross-verification, pick-best, meta-reasoning
- Model configs: single, 3-model, 5-model
"""

import json
import subprocess
import logging
import re
from datetime import datetime
from typing import Optional
from dataclasses import dataclass, asdict

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(message)s',
    datefmt='%H:%M:%S'
)
log = logging.getLogger(__name__)

# =============================================================================
# TEST QUESTIONS
# =============================================================================
QUESTIONS = {
    "factual_fabrication": {
        "question": "What percentage of Fortune 500 CEOs have Harvard MBAs specifically? Cite your source.",
        "type": "unverifiable_fabrication_risk",
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

# =============================================================================
# PROMPT VARIATIONS
# =============================================================================
PROMPTS = {
    "baseline": "{question}",

    "truth_aware": """EPISTEMIC CALIBRATION:
Your claims will be adversarially challenged. For each substantive claim:
- A fact-checker will ask: "What evidence would falsify this?"
- Absolute language (cannot, will not, always, never) is easily falsified
- Quantitative claims without sources will be challenged

TO RESPOND WELL:
- Use comparative language where appropriate ("more likely", "tends to")
- Distinguish well-supported claims from plausible-but-uncertain
- Be decisive where evidence supports it; hedge only where genuinely uncertain

IMPORTANT: Do not over-hedge. The goal is CALIBRATED confidence, not maximum hedging.

---

{question}""",

    "anti_fabrication": """IMPORTANT GUIDELINES:
- If you're uncertain about a specific fact, acknowledge the uncertainty rather than guessing
- Only cite sources you're confident exist - it's better to say "based on my understanding" than to fabricate
- Being honestly uncertain is valued over false confidence
- Your response will be evaluated on accuracy and appropriate confidence calibration

{question}""",

    "combined": """EPISTEMIC CALIBRATION:
Your claims will be adversarially challenged. For each substantive claim:
- A fact-checker will ask: "What evidence would falsify this?"
- Absolute language is easily falsified by counterexamples
- Quantitative claims without sources will be challenged

GUIDELINES:
- If uncertain about a specific fact, acknowledge uncertainty rather than guessing
- Only cite sources you're confident exist
- Being honestly uncertain is valued over false confidence
- Use comparative language where appropriate
- Be decisive where evidence supports it; hedge only where genuinely uncertain

---

{question}"""
}

# =============================================================================
# VERIFICATION STAGE PROMPTS
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
# SYNTHESIS METHODS
# =============================================================================
SYNTHESIS_PROMPTS = {
    "naive": """You are synthesizing responses from multiple AI models into one superior response.

MODEL RESPONSES:
{responses}

QUESTION: {question}

Synthesize these into the best possible response:""",

    "cross_verification": """You are integrating responses from multiple AI models.

CRITICAL RULES:
1. CORROBORATION REQUIRED: Only include specific numbers, statistics, or citations if 2+ models agree
2. PRESERVE UNCERTAINTY: If models agree they can't verify something, preserve that
3. TRUST CAUTION: If Claude/GPT refuse to provide a figure but another model does, trust the caution
4. CONTESTED TOPICS: Present both sides fairly when models genuinely disagree on opinion

MODEL RESPONSES:
{responses}

QUESTION: {question}

Create integrated response using only corroborated claims:""",

    "pick_best": """You are selecting the BEST response from multiple AI models.

Do NOT synthesize. Evaluate each response and pick the one that:
1. Is most HONEST about uncertainty
2. Does NOT fabricate sources or statistics
3. Provides the most HELPFUL guidance given honest limitations

If one response provides specific statistics that others can't verify, prefer the responses that acknowledge uncertainty.

MODEL RESPONSES:
{responses}

QUESTION: {question}

Output ONLY the best response (may lightly edit for clarity):""",

    "meta_reasoning": """You are synthesizing using meta-reasoning about model behavior.

INSIGHT: When asking about specific statistics, some models fabricate confident-sounding answers while others honestly say "I don't know."

REASONING APPROACH:
- If 2+ models express uncertainty about a claim but 1 gives specifics, the specific is likely fabricated
- If a source were real and verifiable, multiple models would find it
- Agreement signals reliability; disagreement on facts signals fabrication risk

MODEL RESPONSES:
{responses}

QUESTION: {question}

Apply meta-reasoning to create an honest synthesis:""",

    "adversarial_verification": """You are synthesizing AND fact-checking responses.

STEP 1: Identify SPECIFIC CLAIMS (numbers, sources, dates)
STEP 2: Check if claims are CORROBORATED by other models
STEP 3: If a claim appears in only one response and others can't verify, REJECT it
STEP 4: Build synthesis using only verified/corroborated claims

MODEL RESPONSES:
{responses}

QUESTION: {question}

First verify claims, then synthesize:"""
}

FINAL_VERIFICATION_PROMPT = """You are performing final verification on this response.

YOUR ROLE: Verify quality, don't rewrite content.

CHECK:
1. Does it avoid presenting unverified claims as fact?
2. Is uncertainty appropriately signaled?
3. Is the reasoning sound and conclusions well-supported?
4. Is it helpful and actionable?

RESPONSE TO VERIFY:
{response}

QUESTION: {question}

If it passes verification, output with minimal changes.
If there are issues, fix them and note what you changed."""

# =============================================================================
# MODEL CONFIGURATIONS
# =============================================================================
MODEL_CONFIGS = {
    "single_claude": ["claude"],
    "single_gpt": ["gpt"],
    "3_models": ["claude", "gpt", "gemini"],
    "5_models": ["claude", "gpt", "gemini", "grok", "deepseek"],
}

# =============================================================================
# PIPELINE CONFIGURATIONS
# =============================================================================
@dataclass
class PipelineConfig:
    name: str
    prompt_type: str
    model_config: str
    use_pre_synthesis_critique: bool  # Each model critiques its response BEFORE synthesis
    use_self_critique: bool  # Post-synthesis self-critique
    use_reasoning_verify: bool
    synthesis_method: Optional[str]  # None for single model
    use_final_verify: bool

    def is_multi_model(self) -> bool:
        return self.model_config in ["3_models", "5_models"]

# Define all pipeline configurations to test
# Format: (name, prompt, models, pre_crit, post_crit, reason_verify, synthesis, final_verify)
PIPELINE_CONFIGS = [
    # === SINGLE MODEL BASELINES ===
    PipelineConfig("baseline_claude", "baseline", "single_claude", False, False, False, None, False),
    PipelineConfig("baseline_gpt", "baseline", "single_gpt", False, False, False, None, False),

    # === PROMPT VARIATIONS (single model) ===
    PipelineConfig("claude_truth_aware", "truth_aware", "single_claude", False, False, False, None, False),
    PipelineConfig("claude_anti_fab", "anti_fabrication", "single_claude", False, False, False, None, False),
    PipelineConfig("claude_combined_prompt", "combined", "single_claude", False, False, False, None, False),

    # === VERIFICATION STAGES (single model) ===
    PipelineConfig("claude_selfcrit", "combined", "single_claude", False, True, False, None, False),
    PipelineConfig("claude_selfcrit_reason", "combined", "single_claude", False, True, True, None, False),
    PipelineConfig("claude_full_verify", "combined", "single_claude", False, True, True, None, True),

    # === MULTI-MODEL SYNTHESIS (3 models) - NO verification ===
    PipelineConfig("3m_naive", "combined", "3_models", False, False, False, "naive", False),
    PipelineConfig("3m_cross_verify", "combined", "3_models", False, False, False, "cross_verification", False),
    PipelineConfig("3m_pick_best", "combined", "3_models", False, False, False, "pick_best", False),
    PipelineConfig("3m_meta_reason", "combined", "3_models", False, False, False, "meta_reasoning", False),
    PipelineConfig("3m_adversarial", "combined", "3_models", False, False, False, "adversarial_verification", False),

    # === 3 MODELS + PRE-SYNTHESIS CRITIQUE (each model self-critiques BEFORE synthesis) ===
    PipelineConfig("3m_precrit_naive", "combined", "3_models", True, False, False, "naive", False),
    PipelineConfig("3m_precrit_cross", "combined", "3_models", True, False, False, "cross_verification", False),
    PipelineConfig("3m_precrit_adversarial", "combined", "3_models", True, False, False, "adversarial_verification", False),

    # === 3 MODELS + POST-SYNTHESIS VERIFICATION ===
    PipelineConfig("3m_cross_postverify", "combined", "3_models", False, True, True, "cross_verification", False),
    PipelineConfig("3m_cross_final", "combined", "3_models", False, False, False, "cross_verification", True),

    # === FULL PIPELINE: Pre-crit + Synthesis + Post-verify + Final ===
    PipelineConfig("3m_precrit_cross_full", "combined", "3_models", True, True, True, "cross_verification", True),
    PipelineConfig("3m_precrit_adversarial_full", "combined", "3_models", True, True, True, "adversarial_verification", True),
    PipelineConfig("3m_precrit_meta_full", "combined", "3_models", True, True, True, "meta_reasoning", True),

    # === 5 MODEL COMPARISON ===
    PipelineConfig("5m_naive", "combined", "5_models", False, False, False, "naive", False),
    PipelineConfig("5m_cross_verify", "combined", "5_models", False, False, False, "cross_verification", False),
    PipelineConfig("5m_precrit_cross", "combined", "5_models", True, False, False, "cross_verification", False),
    PipelineConfig("5m_precrit_cross_full", "combined", "5_models", True, True, True, "cross_verification", True),

    # === HYBRID APPROACHES ===
    PipelineConfig("3m_pick_then_verify", "combined", "3_models", False, True, True, "pick_best", False),
    PipelineConfig("3m_precrit_pick_full", "combined", "3_models", True, True, True, "pick_best", True),

    # === ABLATIONS: Different prompt + full pipeline ===
    PipelineConfig("3m_baseline_prompt_full", "baseline", "3_models", True, True, True, "cross_verification", True),
    PipelineConfig("3m_truth_aware_full", "truth_aware", "3_models", True, True, True, "cross_verification", True),
]

# =============================================================================
# CORE FUNCTIONS
# =============================================================================

def query_model(prompt: str, model: str = "claude") -> str:
    """Query a single model."""
    cmd = ["minds", "ask", "--model", model, "-y", prompt]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    return result.stdout.strip()


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
    """Judge response quality with detailed scores."""
    prompt = f"""Rate this response 0-10 on each dimension. Be critical and precise.

Question: {question}

Response:
{response}

STYLE (0-10): Natural flow, clarity, appropriate length, not overly structured
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


def run_pipeline(config: PipelineConfig, question: str) -> dict:
    """Run a single pipeline configuration and return per-stage results."""
    stages = []
    models = MODEL_CONFIGS[config.model_config]

    # STAGE 1: Initial query with prompt
    log.info(f"    Stage 1: Initial query ({config.prompt_type} prompt, {len(models)} model(s))")
    prompt = PROMPTS[config.prompt_type].format(question=question)

    if config.is_multi_model():
        # Query each model
        model_responses = {}
        for model in models:
            response = query_model(prompt, model)
            model_responses[model] = extract_response_text(response)

        # Score each model's response
        model_scores = {}
        for model, response in model_responses.items():
            scores = judge_response(response, question)
            model_scores[model] = {
                "response": response[:300] + "..." if len(response) > 300 else response,
                "scores": scores,
                "avg": sum(scores.values()) / 3
            }

        stages.append({
            "stage": "1_initial_multi",
            "model_responses": model_scores
        })

        # STAGE 1.5: Pre-synthesis self-critique (each model critiques its own response)
        if config.use_pre_synthesis_critique:
            log.info("    Stage 1.5: Pre-synthesis self-critique (each model)")
            critiqued_responses = {}
            critiqued_scores = {}
            for model, response in model_responses.items():
                critique_prompt = SELF_CRITIQUE_PROMPT.format(response=response)
                critiqued = query_model(critique_prompt, model)
                critiqued_responses[model] = extract_response_text(critiqued)
                scores = judge_response(critiqued_responses[model], question)
                critiqued_scores[model] = {
                    "response": critiqued_responses[model][:300] + "...",
                    "scores": scores,
                    "avg": sum(scores.values()) / 3
                }
            model_responses = critiqued_responses  # Use critiqued for synthesis
            stages.append({
                "stage": "1.5_pre_synthesis_critique",
                "model_responses": critiqued_scores
            })

        # STAGE 2: Synthesis
        log.info(f"    Stage 2: Synthesis ({config.synthesis_method})")
        formatted_responses = "\n\n".join([
            f"**{m.upper()}:**\n{r}" for m, r in model_responses.items()
        ])

        synth_prompt = SYNTHESIS_PROMPTS[config.synthesis_method].format(
            responses=formatted_responses,
            question=question
        )
        current_response = query_model(synth_prompt, "claude")
        current_response = extract_response_text(current_response)

        synth_scores = judge_response(current_response, question)
        stages.append({
            "stage": "2_synthesis",
            "method": config.synthesis_method,
            "response": current_response[:300] + "...",
            "scores": synth_scores,
            "avg": sum(synth_scores.values()) / 3
        })
    else:
        # Single model
        current_response = query_model(prompt, models[0])
        current_response = extract_response_text(current_response)

        initial_scores = judge_response(current_response, question)
        stages.append({
            "stage": "1_initial",
            "model": models[0],
            "response": current_response[:300] + "...",
            "scores": initial_scores,
            "avg": sum(initial_scores.values()) / 3
        })

    # STAGE 3: Post-synthesis self-critique (optional)
    if config.use_self_critique:
        log.info("    Stage 3: Post-synthesis self-critique")
        critique_prompt = SELF_CRITIQUE_PROMPT.format(response=current_response)
        current_response = query_model(critique_prompt, "claude")
        current_response = extract_response_text(current_response)

        critique_scores = judge_response(current_response, question)
        stages.append({
            "stage": "3_self_critique",
            "response": current_response[:300] + "...",
            "scores": critique_scores,
            "avg": sum(critique_scores.values()) / 3
        })

    # STAGE 4: Reasoning verification (optional)
    if config.use_reasoning_verify:
        log.info("    Stage 4: Reasoning verification")
        verify_prompt = REASONING_VERIFICATION_PROMPT.format(response=current_response)
        current_response = query_model(verify_prompt, "claude")
        current_response = extract_response_text(current_response)

        verify_scores = judge_response(current_response, question)
        stages.append({
            "stage": "4_reasoning_verify",
            "response": current_response[:300] + "...",
            "scores": verify_scores,
            "avg": sum(verify_scores.values()) / 3
        })

    # STAGE 5: Final verification (optional)
    if config.use_final_verify:
        log.info("    Stage 5: Final verification")
        final_prompt = FINAL_VERIFICATION_PROMPT.format(
            response=current_response,
            question=question
        )
        current_response = query_model(final_prompt, "claude")
        current_response = extract_response_text(current_response)

        final_scores = judge_response(current_response, question)
        stages.append({
            "stage": "5_final_verify",
            "response": current_response[:300] + "...",
            "scores": final_scores,
            "avg": sum(final_scores.values()) / 3
        })

    # Get final scores
    final_stage = stages[-1]

    return {
        "config": asdict(config),
        "stages": stages,
        "final_scores": final_stage["scores"],
        "final_avg": final_stage["avg"],
        "final_response": current_response[:500] + "..." if len(current_response) > 500 else current_response
    }


def run_experiment():
    """Run the comprehensive experiment."""
    results = {
        "timestamp": datetime.now().isoformat(),
        "experiment": "comprehensive_v1",
        "total_configs": len(PIPELINE_CONFIGS),
        "questions": {}
    }

    log.info("=" * 70)
    log.info("COMPREHENSIVE VERIFICATION EXPERIMENT")
    log.info(f"Testing {len(PIPELINE_CONFIGS)} pipeline configurations")
    log.info(f"Across {len(QUESTIONS)} question types")
    log.info("=" * 70)

    for q_name, q_data in QUESTIONS.items():
        log.info(f"\n{'='*70}")
        log.info(f"QUESTION: {q_name} ({q_data['type']})")
        log.info(f"{'='*70}")

        results["questions"][q_name] = {
            "question": q_data["question"],
            "type": q_data["type"],
            "pipelines": {}
        }

        for config in PIPELINE_CONFIGS:
            log.info(f"\n  Pipeline: {config.name}")
            try:
                pipeline_result = run_pipeline(config, q_data["question"])
                results["questions"][q_name]["pipelines"][config.name] = pipeline_result

                # Log final scores
                s = pipeline_result["final_scores"]
                log.info(f"    FINAL: S:{s['style']} A:{s['adversarial']} R:{s['reasoning']} (avg:{pipeline_result['final_avg']:.1f})")

                # Log stage progression if multiple stages
                if len(pipeline_result["stages"]) > 1:
                    progression = " -> ".join([
                        f"{st['stage'].split('_')[0]}:{st['avg']:.1f}"
                        for st in pipeline_result["stages"]
                    ])
                    log.info(f"    Progression: {progression}")

            except Exception as e:
                log.error(f"    ERROR: {e}")
                results["questions"][q_name]["pipelines"][config.name] = {"error": str(e)}

    # ==========================================================================
    # ANALYSIS
    # ==========================================================================
    log.info(f"\n{'='*70}")
    log.info("ANALYSIS: BEST CONFIGURATIONS")
    log.info(f"{'='*70}")

    for q_name, q_data in results["questions"].items():
        log.info(f"\n{q_name}:")

        # Sort by final average
        sorted_pipes = sorted(
            [(name, data) for name, data in q_data["pipelines"].items()
             if "final_avg" in data],
            key=lambda x: x[1]["final_avg"],
            reverse=True
        )

        log.info(f"  Top 5:")
        for name, data in sorted_pipes[:5]:
            s = data["final_scores"]
            log.info(f"    {name}: S:{s['style']} A:{s['adversarial']} R:{s['reasoning']} (avg:{data['final_avg']:.1f})")

        log.info(f"  Bottom 3:")
        for name, data in sorted_pipes[-3:]:
            s = data["final_scores"]
            log.info(f"    {name}: S:{s['style']} A:{s['adversarial']} R:{s['reasoning']} (avg:{data['final_avg']:.1f})")

    # ==========================================================================
    # STAGE VALUE ANALYSIS
    # ==========================================================================
    log.info(f"\n{'='*70}")
    log.info("ANALYSIS: INCREMENTAL VALUE BY STAGE")
    log.info(f"{'='*70}")

    # Compare claude baseline -> +selfcrit -> +reasoning -> +final
    single_model_progression = [
        "baseline_claude",
        "claude_combined_prompt",
        "claude_selfcrit",
        "claude_selfcrit_reason",
        "claude_full_verify"
    ]

    log.info("\nSingle Model Progression (Claude):")
    for q_name, q_data in results["questions"].items():
        log.info(f"\n  {q_name}:")
        prev_avg = None
        for pipe_name in single_model_progression:
            if pipe_name in q_data["pipelines"] and "final_avg" in q_data["pipelines"][pipe_name]:
                avg = q_data["pipelines"][pipe_name]["final_avg"]
                delta = f" ({avg - prev_avg:+.1f})" if prev_avg else ""
                log.info(f"    {pipe_name}: {avg:.1f}{delta}")
                prev_avg = avg

    # Compare synthesis methods
    synthesis_comparison = [
        "3m_naive",
        "3m_cross_verify",
        "3m_pick_best",
        "3m_meta_reason",
        "3m_adversarial"
    ]

    log.info("\n3-Model Synthesis Method Comparison:")
    for q_name, q_data in results["questions"].items():
        log.info(f"\n  {q_name}:")
        for pipe_name in synthesis_comparison:
            if pipe_name in q_data["pipelines"] and "final_avg" in q_data["pipelines"][pipe_name]:
                data = q_data["pipelines"][pipe_name]
                s = data["final_scores"]
                log.info(f"    {pipe_name}: S:{s['style']} A:{s['adversarial']} R:{s['reasoning']} (avg:{data['final_avg']:.1f})")

    # Compare model counts
    model_count_comparison = [
        "baseline_claude",
        "3m_cross_verify",
        "5m_cross_verify"
    ]

    log.info("\nModel Count Comparison (cross-verification):")
    for q_name, q_data in results["questions"].items():
        log.info(f"\n  {q_name}:")
        for pipe_name in model_count_comparison:
            if pipe_name in q_data["pipelines"] and "final_avg" in q_data["pipelines"][pipe_name]:
                data = q_data["pipelines"][pipe_name]
                s = data["final_scores"]
                log.info(f"    {pipe_name}: S:{s['style']} A:{s['adversarial']} R:{s['reasoning']} (avg:{data['final_avg']:.1f})")

    # ==========================================================================
    # OVERALL RANKINGS
    # ==========================================================================
    log.info(f"\n{'='*70}")
    log.info("OVERALL RANKINGS (averaged across all questions)")
    log.info(f"{'='*70}")

    # Aggregate scores
    pipeline_totals = {}
    for q_name, q_data in results["questions"].items():
        for pipe_name, pipe_data in q_data["pipelines"].items():
            if "final_avg" in pipe_data:
                if pipe_name not in pipeline_totals:
                    pipeline_totals[pipe_name] = {"total": 0, "count": 0, "scores": {"style": 0, "adversarial": 0, "reasoning": 0}}
                pipeline_totals[pipe_name]["total"] += pipe_data["final_avg"]
                pipeline_totals[pipe_name]["count"] += 1
                for dim in ["style", "adversarial", "reasoning"]:
                    pipeline_totals[pipe_name]["scores"][dim] += pipe_data["final_scores"][dim]

    # Calculate averages and sort
    for pipe_name, data in pipeline_totals.items():
        data["avg"] = data["total"] / data["count"]
        for dim in ["style", "adversarial", "reasoning"]:
            data["scores"][dim] /= data["count"]

    sorted_overall = sorted(pipeline_totals.items(), key=lambda x: x[1]["avg"], reverse=True)

    log.info(f"\n{'Pipeline':<30} | {'Style':>5} | {'Adv':>5} | {'Rsn':>5} | {'Avg':>5}")
    log.info("-" * 60)
    for pipe_name, data in sorted_overall:
        s = data["scores"]
        log.info(f"{pipe_name:<30} | {s['style']:>5.1f} | {s['adversarial']:>5.1f} | {s['reasoning']:>5.1f} | {data['avg']:>5.1f}")

    # Save results
    output_file = "/home/keeva/socrates/experiments/experiment_results_comprehensive_v1.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    log.info(f"\nResults saved to {output_file}")

    return results


if __name__ == "__main__":
    run_experiment()

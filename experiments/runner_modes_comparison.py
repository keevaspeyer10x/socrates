#!/usr/bin/env python3
"""
Comparative experiment for minds CLI modes.

Compares:
- simple: Basic minds query (3 models + synthesis)
- debate: minds debate mode (multi-round)
- rigor: minds --rigor mode (truth-aware prompting)
- deep: minds --deep mode (pre-crit + cross-verify)
- gpt-solo: Single GPT-4 query
- opus-solo: Single Claude (Opus) query

Tracks time and cost for each mode.
"""

import json
import subprocess
import logging
import re
import time
from datetime import datetime
from dataclasses import dataclass, asdict, field
from typing import Optional

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(message)s',
    datefmt='%H:%M:%S'
)
log = logging.getLogger(__name__)

# =============================================================================
# TEST QUESTIONS
# =============================================================================
QUESTIONS = [
    {
        "id": "fabrication",
        "question": "What percentage of Fortune 500 CEOs have Harvard MBAs specifically? Cite your source.",
        "type": "fabrication_risk",
        "notes": "Tests whether mode handles unverifiable statistics appropriately"
    },
    {
        "id": "factual",
        "question": "What were the key technical causes of the 2024 CrowdStrike outage?",
        "type": "factual_verifiable",
        "notes": "Models should agree on documented facts"
    },
    {
        "id": "contested",
        "question": "When should you use microservices vs monolith architecture?",
        "type": "contested_opinion",
        "notes": "Legitimate disagreement, should present both sides"
    }
]


# =============================================================================
# MODE CONFIGURATIONS
# =============================================================================
@dataclass
class ModeConfig:
    name: str
    command: list[str]
    description: str


MODES = [
    ModeConfig(
        name="simple",
        command=["minds", "ask", "-y"],
        description="Basic multi-model synthesis"
    ),
    ModeConfig(
        name="rigor",
        command=["minds", "ask", "--rigor", "-y"],
        description="Truth-aware prompting"
    ),
    ModeConfig(
        name="deep",
        command=["minds", "ask", "--deep", "-y"],
        description="Pre-critique + cross-verification synthesis"
    ),
    ModeConfig(
        name="debate",
        command=["minds", "debate", "-y"],
        description="Multi-round debate mode"
    ),
    ModeConfig(
        name="gpt_solo",
        command=["minds", "ask", "--model", "gpt", "-y"],
        description="Single GPT-4 query"
    ),
    ModeConfig(
        name="opus_solo",
        command=["minds", "ask", "--model", "claude", "-y"],
        description="Single Claude (Opus) query"
    ),
]


# =============================================================================
# RESULT DATA STRUCTURES
# =============================================================================
@dataclass
class ModeResult:
    mode: str
    question_id: str
    response: str
    time_seconds: float
    cost_usd: float
    scores: dict = field(default_factory=dict)
    raw_output: str = ""
    error: Optional[str] = None


# =============================================================================
# CORE FUNCTIONS
# =============================================================================

def extract_cost_from_output(output: str) -> float:
    """Extract cost from minds CLI output."""
    # Look for patterns like "Cost: $0.0685" or "cost: $0.0123"
    match = re.search(r'[Cc]ost:\s*\$?([\d.]+)', output)
    if match:
        return float(match.group(1))
    return 0.0


def extract_response_from_output(output: str) -> str:
    """Extract the main response text from minds CLI output."""
    lines = output.split('\n')
    content_lines = []
    in_box = False

    for line in lines:
        # Detect panel/box boundaries
        if '─' in line and ('╭' in line or '╰' in line):
            in_box = '╭' in line
            continue
        if in_box:
            # Clean up box characters
            cleaned = re.sub(r'^[│\s]+', '', line)
            cleaned = re.sub(r'[│\s]+$', '', cleaned)
            if cleaned:
                content_lines.append(cleaned)

    return '\n'.join(content_lines) if content_lines else output


def run_mode(config: ModeConfig, question: str, timeout: int = 300) -> ModeResult:
    """Run a single mode configuration and capture results."""
    cmd = config.command + [question]

    start_time = time.time()
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        elapsed = time.time() - start_time
        output = result.stdout + result.stderr

        response = extract_response_from_output(result.stdout)
        cost = extract_cost_from_output(output)

        return ModeResult(
            mode=config.name,
            question_id="",  # Will be set by caller
            response=response,
            time_seconds=round(elapsed, 2),
            cost_usd=cost,
            raw_output=output[:5000],  # Truncate for storage
            error=None if result.returncode == 0 else f"Exit code: {result.returncode}"
        )
    except subprocess.TimeoutExpired:
        elapsed = time.time() - start_time
        return ModeResult(
            mode=config.name,
            question_id="",
            response="",
            time_seconds=round(elapsed, 2),
            cost_usd=0.0,
            raw_output="",
            error="Timeout"
        )
    except Exception as e:
        elapsed = time.time() - start_time
        return ModeResult(
            mode=config.name,
            question_id="",
            response="",
            time_seconds=round(elapsed, 2),
            cost_usd=0.0,
            raw_output="",
            error=str(e)
        )


def judge_response(response: str, question: str) -> dict:
    """Judge response quality with detailed scores using Claude."""
    prompt = f"""Rate this response 0-10 on each dimension. Be critical and precise.

Question: {question}

Response:
{response[:3000]}

STYLE (0-10): Natural flow, clarity, appropriate length, not overly structured
ADVERSARIAL (0-10): Would survive fact-checking? No fabrication? Honest about uncertainty?
REASONING (0-10): Clear logic? Conclusions well-supported? Decisive where appropriate?

Output JSON only: {{"style": N, "adversarial": N, "reasoning": N}}"""

    cmd = ["minds", "ask", "--model", "claude", "-y", prompt]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        output = result.stdout

        # Extract JSON from response
        match = re.search(r'\{[^{}]*"style"[^{}]*\}', output, re.DOTALL)
        if match:
            return json.loads(re.sub(r'\s+', ' ', match.group()))
    except Exception as e:
        log.warning(f"Judge failed: {e}")

    return {"style": 5, "adversarial": 5, "reasoning": 5}


def run_experiment(questions: list[dict] = None, modes: list[ModeConfig] = None):
    """Run the full comparative experiment."""
    if questions is None:
        questions = QUESTIONS
    if modes is None:
        modes = MODES

    results = []

    log.info(f"=== Starting Modes Comparison Experiment ===")
    log.info(f"Questions: {len(questions)}, Modes: {len(modes)}")

    for q_idx, question_data in enumerate(questions):
        qid = question_data["id"]
        question = question_data["question"]

        log.info(f"\n[{q_idx+1}/{len(questions)}] Question: {qid}")
        log.info(f"  {question[:60]}...")

        for m_idx, mode in enumerate(modes):
            log.info(f"  [{m_idx+1}/{len(modes)}] Mode: {mode.name} ({mode.description})")

            result = run_mode(mode, question)
            result.question_id = qid

            if result.error:
                log.warning(f"    ERROR: {result.error}")
            else:
                log.info(f"    Time: {result.time_seconds}s, Cost: ${result.cost_usd:.4f}")

            # Judge the response if successful
            if result.response and not result.error:
                log.info(f"    Judging response...")
                result.scores = judge_response(result.response, question)
                avg_score = sum(result.scores.values()) / 3
                log.info(f"    Scores: S:{result.scores['style']} A:{result.scores['adversarial']} R:{result.scores['reasoning']} (avg: {avg_score:.1f})")

            results.append(asdict(result))

    return results


def print_summary(results: list[dict]):
    """Print a summary table of results."""
    # Group by mode
    by_mode = {}
    for r in results:
        mode = r["mode"]
        if mode not in by_mode:
            by_mode[mode] = {
                "times": [],
                "costs": [],
                "scores": {"style": [], "adversarial": [], "reasoning": []},
                "errors": 0
            }

        if r["error"]:
            by_mode[mode]["errors"] += 1
        else:
            by_mode[mode]["times"].append(r["time_seconds"])
            by_mode[mode]["costs"].append(r["cost_usd"])
            if r["scores"]:
                for key in ["style", "adversarial", "reasoning"]:
                    if key in r["scores"]:
                        by_mode[mode]["scores"][key].append(r["scores"][key])

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"{'Mode':<12} {'Avg Time':>10} {'Avg Cost':>10} {'Style':>7} {'Advers':>7} {'Reason':>7} {'Avg':>7} {'Errors':>7}")
    print("-" * 80)

    for mode in MODES:
        name = mode.name
        data = by_mode.get(name, {"times": [], "costs": [], "scores": {"style": [], "adversarial": [], "reasoning": []}, "errors": 0})

        avg_time = sum(data["times"]) / len(data["times"]) if data["times"] else 0
        avg_cost = sum(data["costs"]) / len(data["costs"]) if data["costs"] else 0

        s_scores = data["scores"]["style"]
        a_scores = data["scores"]["adversarial"]
        r_scores = data["scores"]["reasoning"]

        avg_s = sum(s_scores) / len(s_scores) if s_scores else 0
        avg_a = sum(a_scores) / len(a_scores) if a_scores else 0
        avg_r = sum(r_scores) / len(r_scores) if r_scores else 0
        overall = (avg_s + avg_a + avg_r) / 3 if (s_scores and a_scores and r_scores) else 0

        print(f"{name:<12} {avg_time:>9.1f}s ${avg_cost:>8.4f} {avg_s:>7.1f} {avg_a:>7.1f} {avg_r:>7.1f} {overall:>7.1f} {data['errors']:>7}")

    print("=" * 80)


def main():
    """Main entry point."""
    log.info("Starting modes comparison experiment...")

    # Run experiment
    results = run_experiment()

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"/home/keeva/socrates/experiments/modes_comparison_{timestamp}.json"

    with open(output_file, 'w') as f:
        json.dump({
            "timestamp": timestamp,
            "questions": QUESTIONS,
            "modes": [asdict(m) if hasattr(m, '__dataclass_fields__') else {"name": m.name, "command": m.command, "description": m.description} for m in MODES],
            "results": results
        }, f, indent=2)

    log.info(f"\nResults saved to: {output_file}")

    # Print summary
    print_summary(results)


if __name__ == "__main__":
    main()

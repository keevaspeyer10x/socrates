#!/usr/bin/env python3
"""
GPQA Diamond Benchmark Comparison: Multi-model vs Single Model

Compares:
1. minds baseline (5-model synthesis)
2. minds --deep (verification pipeline)
3. minds --rigor (truth-aware prompting)
4. Claude Opus 4.5 solo
5. GPT-5.2 solo

GPQA Diamond: 198 PhD-level science questions (physics, chemistry, biology)
Human expert baseline: 69.7% accuracy

Cost estimates (per full run):
- minds baseline: ~$0.03/q × 198 = ~$6
- minds deep: ~$0.08/q × 198 = ~$16
- minds rigor: ~$0.02/q × 198 = ~$4
- Claude Opus solo: ~$0.02/q × 198 = ~$4
- GPT-5.2 solo: ~$0.02/q × 198 = ~$4

Total for full run: ~$34 (all configs)
Pilot run (20 samples): ~$3-4

Usage:
    # Pilot run (20 samples)
    python experiments/runner_gpqa_comparison.py --samples 20

    # Full run
    python experiments/runner_gpqa_comparison.py --full

    # Single config
    python experiments/runner_gpqa_comparison.py --config minds_baseline --samples 20
"""

import argparse
import json
import logging
import subprocess
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(message)s',
    datefmt='%H:%M:%S'
)
log = logging.getLogger(__name__)

# Configurations to test
CONFIGS = {
    "minds_baseline": {
        "solver": "minds",
        "solver_mode": "baseline",
        "model": "anthropic/claude-opus-4-5-20251101",
        "description": "Multi-model synthesis (5 models)",
        "expected_cost_per_q": 0.03,
    },
    "minds_deep": {
        "solver": "minds",
        "solver_mode": "deep",
        "model": "anthropic/claude-opus-4-5-20251101",
        "description": "Deep verification pipeline (self-critique + cross-verify)",
        "expected_cost_per_q": 0.08,
    },
    "minds_rigor": {
        "solver": "minds",
        "solver_mode": "rigor",
        "model": "anthropic/claude-opus-4-5-20251101",
        "description": "Truth-aware prompting (epistemic calibration)",
        "expected_cost_per_q": 0.04,
    },
    "minds_reasoning": {
        "solver": "minds",
        "solver_mode": "reasoning",
        "model": "anthropic/claude-opus-4-5-20251101",
        "description": "Explicit step-by-step reasoning with cross-model discussion",
        "expected_cost_per_q": 0.05,
    },
    "minds_critique": {
        "solver": "minds",
        "solver_mode": "critique",
        "model": "anthropic/claude-opus-4-5-20251101",
        "description": "Models critique each other, then revise answers",
        "expected_cost_per_q": 0.10,
    },
    "minds_critique2": {
        "solver": "minds",
        "solver_mode": "critique2",
        "model": "anthropic/claude-opus-4-5-20251101",
        "description": "Two rounds of cross-model critique and revision",
        "expected_cost_per_q": 0.18,
    },
    "minds_critique3": {
        "solver": "minds",
        "solver_mode": "critique3",
        "model": "anthropic/claude-opus-4-5-20251101",
        "description": "Three rounds of cross-model critique and revision",
        "expected_cost_per_q": 0.26,
    },
    "minds_debate": {
        "solver": "minds",
        "solver_mode": "debate",
        "model": "anthropic/claude-opus-4-5-20251101",
        "description": "Adversarial debate - argue FOR and AGAINST each option",
        "expected_cost_per_q": 0.12,
    },
    "minds_systematic": {
        "solver": "minds",
        "solver_mode": "systematic",
        "model": "anthropic/claude-opus-4-5-20251101",
        "description": "Systematic evaluation of ALL options before choosing",
        "expected_cost_per_q": 0.04,
    },
    "minds_critique_systematic": {
        "solver": "minds",
        "solver_mode": "critique_systematic",
        "model": "anthropic/claude-opus-4-5-20251101",
        "description": "Systematic eval + critique workflow",
        "expected_cost_per_q": 0.12,
    },
    "minds_critique_challenge": {
        "solver": "minds",
        "solver_mode": "critique_challenge",
        "model": "anthropic/claude-opus-4-5-20251101",
        "description": "Critique + devil's advocate challenge on consensus (3 models: Claude, GPT, Gemini)",
        "expected_cost_per_q": 0.15,
    },
    "claude_solo": {
        "solver": "baseline",
        "solver_mode": "baseline",
        "model": "anthropic/claude-opus-4-5-20251101",
        "description": "Claude Opus 4.5 single model",
        "expected_cost_per_q": 0.02,
    },
    "gpt_solo": {
        "solver": "baseline",
        "solver_mode": "baseline",
        "model": "openai/gpt-5.2",
        "description": "GPT-5.2 single model",
        "expected_cost_per_q": 0.02,
    },
}


@dataclass
class RunResult:
    config_name: str
    run_id: str
    solver: str
    model: str
    samples: int
    passed: int
    pass_rate: float
    total_cost_usd: float
    time_seconds: float
    error: Optional[str] = None


def run_config(
    config_name: str,
    samples: Optional[int] = None,
    sample_ids: Optional[list[int]] = None
) -> RunResult:
    """Run a single configuration."""
    config = CONFIGS[config_name]

    cmd = [
        "socrates-eval", "run", "gpqa",
        "--solver", config["solver"],
        "--model", config["model"],
        "--solver-mode", config.get("solver_mode", "baseline"),
    ]

    if samples and not sample_ids:
        cmd.extend(["--samples", str(samples)])
    elif sample_ids:
        # Create temp file with sample IDs
        ids_file = Path(f"/tmp/gpqa_sample_ids_{config_name}.json")
        ids_file.write_text(json.dumps(sample_ids))
        cmd.extend(["--sample-ids", str(ids_file)])

    log.info(f"Running: {' '.join(cmd)}")
    start_time = time.time()

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=3600,  # 1 hour max
            cwd="/home/keeva/socrates"
        )
        elapsed = time.time() - start_time

        if result.returncode != 0:
            log.error(f"Command failed: {result.stderr}")
            return RunResult(
                config_name=config_name,
                run_id="",
                solver=config["solver"],
                model=config["model"],
                samples=samples or len(sample_ids or []),
                passed=0,
                pass_rate=0.0,
                total_cost_usd=0.0,
                time_seconds=elapsed,
                error=result.stderr[:500]
            )

        # Parse results from output
        output = result.stdout + result.stderr
        run_id = _extract_run_id(output)
        passed, total = _extract_results(output)
        cost = _extract_cost(output)

        return RunResult(
            config_name=config_name,
            run_id=run_id,
            solver=config["solver"],
            model=config["model"],
            samples=total,
            passed=passed,
            pass_rate=passed / total if total > 0 else 0.0,
            total_cost_usd=cost,
            time_seconds=elapsed
        )

    except subprocess.TimeoutExpired:
        return RunResult(
            config_name=config_name,
            run_id="",
            solver=config["solver"],
            model=config["model"],
            samples=samples or len(sample_ids or []),
            passed=0,
            pass_rate=0.0,
            total_cost_usd=0.0,
            time_seconds=3600,
            error="Timeout"
        )
    except Exception as e:
        return RunResult(
            config_name=config_name,
            run_id="",
            solver=config["solver"],
            model=config["model"],
            samples=samples or len(sample_ids or []),
            passed=0,
            pass_rate=0.0,
            total_cost_usd=0.0,
            time_seconds=time.time() - start_time,
            error=str(e)
        )


def _extract_run_id(output: str) -> str:
    """Extract run ID from output."""
    import re
    match = re.search(r'Run ID:\s*(\S+)', output)
    return match.group(1) if match else ""


def _extract_results(output: str) -> tuple[int, int]:
    """Extract passed/total from output."""
    import re
    match = re.search(r'Results:\s*(\d+)/(\d+)\s+passed', output)
    if match:
        return int(match.group(1)), int(match.group(2))
    return 0, 0


def _extract_cost(output: str) -> float:
    """Extract cost from output."""
    import re
    match = re.search(r'Cost:\s*\$?([\d.]+)', output)
    return float(match.group(1)) if match else 0.0


def print_results(results: list[RunResult]):
    """Print comparison table."""
    print("\n" + "=" * 100)
    print("GPQA DIAMOND COMPARISON RESULTS")
    print("=" * 100)
    print(f"{'Config':<20} {'Solver':<12} {'Pass Rate':>12} {'Passed':>10} {'Cost':>10} {'Time':>10}")
    print("-" * 100)

    for r in results:
        if r.error:
            print(f"{r.config_name:<20} {r.solver:<12} {'ERROR':>12} {'-':>10} {'-':>10} {r.time_seconds:>9.0f}s")
        else:
            print(f"{r.config_name:<20} {r.solver:<12} {r.pass_rate:>11.1%} {r.passed:>10}/{r.samples:<3} ${r.total_cost_usd:>8.4f} {r.time_seconds:>9.0f}s")

    print("=" * 100)

    # Analysis
    valid_results = [r for r in results if not r.error]
    if valid_results:
        print("\nANALYSIS:")
        print("-" * 50)

        # Best accuracy
        by_accuracy = sorted(valid_results, key=lambda x: x.pass_rate, reverse=True)
        print(f"Highest accuracy: {by_accuracy[0].config_name} ({by_accuracy[0].pass_rate:.1%})")

        # Best cost efficiency
        with_cost = [r for r in valid_results if r.total_cost_usd > 0]
        if with_cost:
            by_efficiency = sorted(with_cost, key=lambda x: x.pass_rate / x.total_cost_usd, reverse=True)
            eff = by_efficiency[0].pass_rate / by_efficiency[0].total_cost_usd
            print(f"Best cost efficiency: {by_efficiency[0].config_name} ({eff:.0f}%/$ for ${by_efficiency[0].total_cost_usd:.4f})")

        # Compare multi-model vs single
        multi_results = [r for r in valid_results if r.solver == "minds"]
        single_results = [r for r in valid_results if r.solver == "baseline"]

        if multi_results and single_results:
            best_multi = max(multi_results, key=lambda x: x.pass_rate)
            best_single = max(single_results, key=lambda x: x.pass_rate)
            delta = best_multi.pass_rate - best_single.pass_rate
            print(f"\nMulti-model advantage: {delta:+.1%}")
            print(f"  Best multi-model: {best_multi.config_name} ({best_multi.pass_rate:.1%})")
            print(f"  Best single model: {best_single.config_name} ({best_single.pass_rate:.1%})")


def main():
    parser = argparse.ArgumentParser(description="Run GPQA comparison benchmark")
    parser.add_argument("--samples", type=int, default=20, help="Number of samples (default: 20 for pilot)")
    parser.add_argument("--full", action="store_true", help="Run full benchmark (198 samples)")
    parser.add_argument("--config", type=str, help="Run single config only")
    parser.add_argument("--configs", type=str, help="Comma-separated list of configs to run")
    args = parser.parse_args()

    samples = None if args.full else args.samples

    # Determine which configs to run
    if args.config:
        configs_to_run = [args.config]
    elif args.configs:
        configs_to_run = [c.strip() for c in args.configs.split(",")]
    else:
        configs_to_run = list(CONFIGS.keys())

    # Validate configs
    for c in configs_to_run:
        if c not in CONFIGS:
            log.error(f"Unknown config: {c}. Available: {list(CONFIGS.keys())}")
            return

    # Estimate cost
    total_expected = 0
    for c in configs_to_run:
        expected = CONFIGS[c]["expected_cost_per_q"] * (samples or 198)
        total_expected += expected

    log.info(f"Running GPQA comparison")
    log.info(f"  Configs: {configs_to_run}")
    log.info(f"  Samples: {samples or 'all (198)'}")
    log.info(f"  Estimated cost: ${total_expected:.2f}")
    print()

    # Run each config
    results = []
    for config_name in configs_to_run:
        log.info(f"\n{'='*60}")
        log.info(f"Running config: {config_name}")
        log.info(f"Description: {CONFIGS[config_name]['description']}")
        log.info(f"{'='*60}")

        result = run_config(config_name, samples=samples)
        results.append(result)

        if result.error:
            log.error(f"Config {config_name} failed: {result.error}")
        else:
            log.info(f"Config {config_name}: {result.pass_rate:.1%} ({result.passed}/{result.samples}) in {result.time_seconds:.0f}s, ${result.total_cost_usd:.4f}")

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"/home/keeva/socrates/experiments/gpqa_comparison_{timestamp}.json"

    with open(output_file, 'w') as f:
        json.dump({
            "timestamp": timestamp,
            "samples": samples,
            "configs": configs_to_run,
            "results": [asdict(r) for r in results]
        }, f, indent=2)

    log.info(f"\nResults saved to: {output_file}")

    # Print comparison
    print_results(results)


if __name__ == "__main__":
    main()

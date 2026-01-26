#!/usr/bin/env python3
"""
Comprehensive GPQA comparison to understand value at each step.

Tests:
1. Solo models (Claude, GPT, Gemini) - individual baselines
2. Multi-model baseline synthesis - just combine without critique
3. Multi-model critique - add critique workflow
4. Multi-model critique_challenge - add devil's advocate on consensus
5. Multi-model critique_aggressive - always run aggressive challenge

This helps identify:
- How much does multi-model add over solo?
- How much does critique add?
- How much does devil's advocate add?
"""

import subprocess
import json
import time
from pathlib import Path
from datetime import datetime

# Full 198 samples - no sample limitation
CONFIGS = [
    # Solo model baselines (using baseline solver = single model, no multi-model)
    {
        "name": "claude_solo",
        "description": "Claude Opus 4.5 alone",
        "solver": "baseline",
        "model": "anthropic/claude-opus-4-5-20251101",
        "solver_mode": None,
    },
    {
        "name": "gpt_solo",
        "description": "GPT-5.2 alone",
        "solver": "baseline",
        "model": "openai/gpt-5.2",
        "solver_mode": None,
    },
    {
        "name": "gemini_solo",
        "description": "Gemini 2.5 Pro alone",
        "solver": "baseline",
        "model": "google/gemini-2.5-pro",
        "solver_mode": None,
    },
    # Multi-model configurations
    {
        "name": "minds_baseline",
        "description": "Multi-model baseline (no critique)",
        "solver": "minds",
        "model": "anthropic/claude-opus-4-5-20251101",
        "solver_mode": "baseline",
    },
    {
        "name": "minds_critique",
        "description": "Multi-model with critique workflow",
        "solver": "minds",
        "model": "anthropic/claude-opus-4-5-20251101",
        "solver_mode": "critique",
    },
    {
        "name": "minds_critique_challenge",
        "description": "Critique + devil's advocate on consensus",
        "solver": "minds",
        "model": "anthropic/claude-opus-4-5-20251101",
        "solver_mode": "critique_challenge",
    },
    {
        "name": "minds_critique_aggressive",
        "description": "Critique + always aggressive challenge",
        "solver": "minds",
        "model": "anthropic/claude-opus-4-5-20251101",
        "solver_mode": "critique_aggressive",
    },
]


def run_config(config: dict, samples: int | None = None) -> dict:
    """Run a single configuration and return results."""
    name = config["name"]
    solver = config["solver"]
    model = config["model"]
    mode = config.get("solver_mode")

    cmd = [
        "socrates-eval", "run", "gpqa",
        "--solver", solver,
        "--model", model,
    ]

    if mode:
        cmd.extend(["--solver-mode", mode])

    if samples:
        cmd.extend(["--samples", str(samples)])

    print(f"\n{'='*60}")
    print(f"Running: {name}")
    print(f"Description: {config['description']}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}")

    start_time = time.time()
    result = subprocess.run(cmd, capture_output=True, text=True)
    elapsed = time.time() - start_time

    # Parse output for results
    output = result.stdout + result.stderr
    print(output[-2000:] if len(output) > 2000 else output)

    # Extract accuracy from output
    accuracy = None
    passed = None
    total = None
    cost = None

    import re

    # Look for "Results: X/Y passed (Z%)"
    match = re.search(r'Results:\s*(\d+)/(\d+)\s*passed\s*\((\d+\.?\d*)%\)', output)
    if match:
        passed = int(match.group(1))
        total = int(match.group(2))
        accuracy = float(match.group(3))

    # Look for cost
    match = re.search(r'Cost:\s*\$?([\d.]+)', output)
    if match:
        cost = float(match.group(1))

    return {
        "name": name,
        "description": config["description"],
        "accuracy": accuracy,
        "passed": passed,
        "total": total,
        "cost": cost,
        "time": elapsed,
        "returncode": result.returncode,
    }


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--samples", type=int, default=None,
                        help="Number of samples (default: all 198)")
    parser.add_argument("--configs", nargs="+", default=None,
                        help="Specific configs to run (e.g., claude_solo gpt_solo)")
    parser.add_argument("--skip-solo", action="store_true",
                        help="Skip solo model runs")
    args = parser.parse_args()

    configs_to_run = CONFIGS

    if args.configs:
        configs_to_run = [c for c in CONFIGS if c["name"] in args.configs]
    elif args.skip_solo:
        configs_to_run = [c for c in CONFIGS if not c["name"].endswith("_solo")]

    results = []

    print(f"\n{'#'*60}")
    print(f"# GPQA Full Comparison")
    print(f"# Samples: {args.samples or 'ALL (198)'}")
    print(f"# Configs: {[c['name'] for c in configs_to_run]}")
    print(f"# Started: {datetime.now().isoformat()}")
    print(f"{'#'*60}")

    for config in configs_to_run:
        try:
            result = run_config(config, args.samples)
            results.append(result)
        except Exception as e:
            print(f"ERROR running {config['name']}: {e}")
            results.append({
                "name": config["name"],
                "error": str(e),
            })

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = Path(f"experiments/full_comparison_{timestamp}.json")
    output_file.write_text(json.dumps(results, indent=2))

    # Print summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    print(f"{'Config':<30} {'Accuracy':>10} {'Passed':>10} {'Cost':>12} {'Time':>10}")
    print(f"{'-'*80}")

    for r in results:
        name = r.get("name", "?")
        acc = f"{r.get('accuracy', 0):.1f}%" if r.get('accuracy') else "N/A"
        passed = f"{r.get('passed', 0)}/{r.get('total', 0)}" if r.get('passed') else "N/A"
        cost = f"${r.get('cost', 0):.2f}" if r.get('cost') else "N/A"
        time_s = f"{r.get('time', 0):.0f}s" if r.get('time') else "N/A"
        print(f"{name:<30} {acc:>10} {passed:>10} {cost:>12} {time_s:>10}")

    print(f"\nResults saved to: {output_file}")

    # Calculate value-add at each step
    print(f"\n{'='*80}")
    print("VALUE-ADD ANALYSIS")
    print(f"{'='*80}")

    def get_acc(name):
        for r in results:
            if r.get("name") == name:
                return r.get("accuracy", 0)
        return None

    solo_accs = [get_acc("claude_solo"), get_acc("gpt_solo"), get_acc("gemini_solo")]
    solo_accs = [a for a in solo_accs if a is not None]
    if solo_accs:
        best_solo = max(solo_accs)
        avg_solo = sum(solo_accs) / len(solo_accs)
        print(f"Best solo model: {best_solo:.1f}%")
        print(f"Average solo model: {avg_solo:.1f}%")

    baseline = get_acc("minds_baseline")
    critique = get_acc("minds_critique")
    challenge = get_acc("minds_critique_challenge")
    aggressive = get_acc("minds_critique_aggressive")

    if baseline and solo_accs:
        print(f"\nMulti-model baseline vs best solo: {baseline:.1f}% vs {best_solo:.1f}% ({baseline - best_solo:+.1f}%)")

    if critique and baseline:
        print(f"Critique vs baseline: {critique:.1f}% vs {baseline:.1f}% ({critique - baseline:+.1f}%)")

    if challenge and critique:
        print(f"Challenge vs critique: {challenge:.1f}% vs {critique:.1f}% ({challenge - critique:+.1f}%)")

    if aggressive and challenge:
        print(f"Aggressive vs challenge: {aggressive:.1f}% vs {challenge:.1f}% ({aggressive - challenge:+.1f}%)")


if __name__ == "__main__":
    main()

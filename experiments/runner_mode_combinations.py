#!/usr/bin/env python3
"""
Test all valid minds CLI mode combinations.

Tests combinations of:
- Base modes: (none), --rigor, --deep
- Model selection: --cheap, --fast, (default flagship)
- Single vs multi: --model X, (default multi)

Invalid combinations (tested for proper error handling):
- --deep + --single
- --deep + --model X
- --deep + --quick

Valid combinations to test:
1. minds ask (baseline multi-model)
2. minds ask --rigor (truth-aware multi-model)
3. minds ask --deep (verification pipeline)
4. minds ask --cheap (cheap models)
5. minds ask --fast (fast models)
6. minds ask --rigor --cheap
7. minds ask --rigor --fast
8. minds ask --deep --cheap
9. minds ask --deep --fast
10. minds ask --model claude (single model)
11. minds ask --model claude --rigor
12. minds ask --model claude --cheap
13. minds ask --model claude --fast
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

# Test question (fabrication-risk to test adversarial quality)
TEST_QUESTION = "What percentage of Fortune 500 CEOs have Harvard MBAs? Cite your source."

# Valid mode combinations
VALID_COMBINATIONS = [
    {"name": "baseline", "args": []},
    {"name": "rigor", "args": ["--rigor"]},
    {"name": "deep", "args": ["--deep"]},
    {"name": "cheap", "args": ["--cheap"]},
    {"name": "fast", "args": ["--fast"]},
    {"name": "rigor_cheap", "args": ["--rigor", "--cheap"]},
    {"name": "rigor_fast", "args": ["--rigor", "--fast"]},
    {"name": "deep_cheap", "args": ["--deep", "--cheap"]},
    {"name": "deep_fast", "args": ["--deep", "--fast"]},
    {"name": "single_claude", "args": ["--model", "claude"]},
    {"name": "single_claude_rigor", "args": ["--model", "claude", "--rigor"]},
    {"name": "single_claude_cheap", "args": ["--model", "claude", "--cheap"]},
    {"name": "single_claude_fast", "args": ["--model", "claude", "--fast"]},
]

# Invalid combinations (should error)
INVALID_COMBINATIONS = [
    {"name": "deep_single", "args": ["--deep", "--model", "claude"], "expected_error": "requires multiple models"},
    {"name": "deep_quick", "args": ["--deep", "--quick"], "expected_error": "requires multiple models"},
]


@dataclass
class CombinationResult:
    name: str
    args: list[str]
    success: bool
    time_seconds: float
    cost_usd: float
    response: str = ""
    scores: dict = field(default_factory=dict)
    error: Optional[str] = None


def extract_cost_from_output(output: str) -> float:
    """Extract cost from minds CLI output."""
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
        if '─' in line and ('╭' in line or '╰' in line):
            in_box = '╭' in line
            continue
        if in_box:
            cleaned = re.sub(r'^[│\s]+', '', line)
            cleaned = re.sub(r'[│\s]+$', '', cleaned)
            if cleaned:
                content_lines.append(cleaned)

    return '\n'.join(content_lines) if content_lines else output


def run_combination(combo: dict, question: str, timeout: int = 300) -> CombinationResult:
    """Run a single mode combination."""
    cmd = ["minds", "ask", "-y"] + combo["args"] + [question]

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

        success = result.returncode == 0
        response = extract_response_from_output(result.stdout) if success else ""
        cost = extract_cost_from_output(output)

        return CombinationResult(
            name=combo["name"],
            args=combo["args"],
            success=success,
            time_seconds=round(elapsed, 2),
            cost_usd=cost,
            response=response[:2000],  # Truncate
            error=None if success else output[:500]
        )
    except subprocess.TimeoutExpired:
        elapsed = time.time() - start_time
        return CombinationResult(
            name=combo["name"],
            args=combo["args"],
            success=False,
            time_seconds=round(elapsed, 2),
            cost_usd=0.0,
            error="Timeout"
        )
    except Exception as e:
        elapsed = time.time() - start_time
        return CombinationResult(
            name=combo["name"],
            args=combo["args"],
            success=False,
            time_seconds=round(elapsed, 2),
            cost_usd=0.0,
            error=str(e)
        )


def test_invalid_combination(combo: dict) -> CombinationResult:
    """Test that an invalid combination properly errors."""
    cmd = ["minds", "ask", "-y"] + combo["args"] + [TEST_QUESTION]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10  # Should fail fast
        )
        output = result.stdout + result.stderr

        # Check if it properly rejected
        expected = combo.get("expected_error", "")
        if result.returncode != 0 and expected.lower() in output.lower():
            return CombinationResult(
                name=combo["name"],
                args=combo["args"],
                success=True,  # Success = properly rejected
                time_seconds=0,
                cost_usd=0,
                error=f"Properly rejected: {expected}"
            )
        else:
            return CombinationResult(
                name=combo["name"],
                args=combo["args"],
                success=False,  # Failed to reject
                time_seconds=0,
                cost_usd=0,
                error=f"Should have rejected but didn't: {output[:200]}"
            )
    except Exception as e:
        return CombinationResult(
            name=combo["name"],
            args=combo["args"],
            success=False,
            time_seconds=0,
            cost_usd=0,
            error=str(e)
        )


def judge_response(response: str, question: str) -> dict:
    """Judge response quality."""
    prompt = f"""Rate this response 0-10 on each dimension. Be critical.

Question: {question}

Response:
{response[:3000]}

STYLE (0-10): Natural flow, clarity, not overly hedged
ADVERSARIAL (0-10): Would survive fact-checking? Honest about uncertainty?
REASONING (0-10): Clear logic? Conclusions supported?

Output JSON only: {{"style": N, "adversarial": N, "reasoning": N}}"""

    cmd = ["minds", "ask", "--model", "claude", "-y", prompt]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        match = re.search(r'\{[^{}]*"style"[^{}]*\}', result.stdout, re.DOTALL)
        if match:
            return json.loads(re.sub(r'\s+', ' ', match.group()))
    except Exception as e:
        log.warning(f"Judge failed: {e}")

    return {"style": 5, "adversarial": 5, "reasoning": 5}


def run_experiment():
    """Run the full mode combinations experiment."""
    results = []

    log.info("=== Testing Invalid Combinations (should error) ===")
    for combo in INVALID_COMBINATIONS:
        log.info(f"Testing {combo['name']}...")
        result = test_invalid_combination(combo)
        if result.success:
            log.info(f"  ✓ Properly rejected")
        else:
            log.warning(f"  ✗ {result.error}")
        results.append(asdict(result))

    log.info("\n=== Testing Valid Combinations ===")
    for i, combo in enumerate(VALID_COMBINATIONS):
        log.info(f"[{i+1}/{len(VALID_COMBINATIONS)}] {combo['name']}: {' '.join(combo['args']) or '(default)'}")

        result = run_combination(combo, TEST_QUESTION)

        if result.success:
            log.info(f"  Time: {result.time_seconds}s, Cost: ${result.cost_usd:.4f}")

            # Judge the response
            if result.response:
                log.info(f"  Judging...")
                result.scores = judge_response(result.response, TEST_QUESTION)
                avg = sum(result.scores.values()) / 3
                log.info(f"  Scores: S:{result.scores['style']} A:{result.scores['adversarial']} R:{result.scores['reasoning']} (avg: {avg:.1f})")
        else:
            log.warning(f"  FAILED: {result.error}")

        results.append(asdict(result))

    return results


def print_summary(results: list[dict]):
    """Print summary table."""
    print("\n" + "=" * 100)
    print("MODE COMBINATIONS RESULTS")
    print("=" * 100)
    print(f"{'Combination':<22} {'Time':>8} {'Cost':>10} {'Style':>7} {'Advers':>7} {'Reason':>7} {'Avg':>7} {'Status':<10}")
    print("-" * 100)

    for r in results:
        if not r.get("success", False) and r["name"] in [c["name"] for c in INVALID_COMBINATIONS]:
            # Invalid combo that properly errored
            print(f"{r['name']:<22} {'N/A':>8} {'N/A':>10} {'N/A':>7} {'N/A':>7} {'N/A':>7} {'N/A':>7} {'REJECTED':<10}")
        elif r.get("success", False):
            scores = r.get("scores", {})
            s = scores.get("style", "-")
            a = scores.get("adversarial", "-")
            re = scores.get("reasoning", "-")
            avg = (s + a + re) / 3 if isinstance(s, (int, float)) else "-"
            avg_str = f"{avg:.1f}" if isinstance(avg, float) else avg
            print(f"{r['name']:<22} {r['time_seconds']:>7.1f}s ${r['cost_usd']:>9.4f} {s:>7} {a:>7} {re:>7} {avg_str:>7} {'OK':<10}")
        else:
            print(f"{r['name']:<22} {r['time_seconds']:>7.1f}s {'N/A':>10} {'N/A':>7} {'N/A':>7} {'N/A':>7} {'N/A':>7} {'FAILED':<10}")

    print("=" * 100)

    # Recommendations
    print("\nRECOMMENDATIONS:")
    print("-" * 50)

    valid_results = [r for r in results if r.get("success") and r.get("scores")]
    if valid_results:
        # Sort by adversarial score
        by_adv = sorted(valid_results, key=lambda x: x["scores"].get("adversarial", 0), reverse=True)
        print(f"Best adversarial resistance: {by_adv[0]['name']} (score: {by_adv[0]['scores']['adversarial']})")

        # Sort by cost efficiency (avg score / cost)
        with_cost = [r for r in valid_results if r["cost_usd"] > 0]
        if with_cost:
            by_efficiency = sorted(with_cost, key=lambda x: sum(x["scores"].values()) / 3 / x["cost_usd"], reverse=True)
            print(f"Best cost efficiency: {by_efficiency[0]['name']}")

        # Sort by speed
        by_speed = sorted(valid_results, key=lambda x: x["time_seconds"])
        print(f"Fastest: {by_speed[0]['name']} ({by_speed[0]['time_seconds']}s)")

        # Overall best
        by_overall = sorted(valid_results, key=lambda x: sum(x["scores"].values()) / 3, reverse=True)
        print(f"Best overall quality: {by_overall[0]['name']} (avg: {sum(by_overall[0]['scores'].values())/3:.1f})")


def main():
    log.info("Starting mode combinations experiment...")

    results = run_experiment()

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"/home/keeva/socrates/experiments/mode_combinations_{timestamp}.json"

    with open(output_file, 'w') as f:
        json.dump({
            "timestamp": timestamp,
            "question": TEST_QUESTION,
            "valid_combinations": VALID_COMBINATIONS,
            "invalid_combinations": INVALID_COMBINATIONS,
            "results": results
        }, f, indent=2)

    log.info(f"\nResults saved to: {output_file}")

    print_summary(results)


if __name__ == "__main__":
    main()

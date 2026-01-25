#!/usr/bin/env python3
"""
Full mode combinations test across all question types.

Tests all valid mode combinations across:
- fabrication: Statistics/citations (fabrication risk)
- factual: Documented events (verifiable facts)
- contested: Opinion-based (legitimate disagreement)

Includes consistency analysis (std dev across questions).
"""

import json
import subprocess
import logging
import re
import time
import math
from datetime import datetime
from dataclasses import dataclass, asdict, field
from typing import Optional
from collections import defaultdict

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(message)s',
    datefmt='%H:%M:%S'
)
log = logging.getLogger(__name__)

# Test questions
QUESTIONS = [
    {
        "id": "fabrication",
        "question": "What percentage of Fortune 500 CEOs have Harvard MBAs? Cite your source.",
        "type": "fabrication_risk"
    },
    {
        "id": "factual",
        "question": "What were the key technical causes of the 2024 CrowdStrike outage?",
        "type": "factual_verifiable"
    },
    {
        "id": "contested",
        "question": "When should you use microservices vs monolith architecture?",
        "type": "contested_opinion"
    }
]

# Valid mode combinations to test
MODE_COMBINATIONS = [
    {"name": "baseline", "args": [], "desc": "Default multi-model"},
    {"name": "rigor", "args": ["--rigor"], "desc": "Truth-aware prompting"},
    {"name": "deep", "args": ["--deep"], "desc": "Pre-crit + cross-verify"},
    {"name": "cheap", "args": ["--cheap"], "desc": "Budget models"},
    {"name": "fast", "args": ["--fast"], "desc": "Fast models + 10s timeout"},
    {"name": "rigor_cheap", "args": ["--rigor", "--cheap"], "desc": "Truth-aware + budget"},
    {"name": "rigor_fast", "args": ["--rigor", "--fast"], "desc": "Truth-aware + fast"},
    {"name": "deep_cheap", "args": ["--deep", "--cheap"], "desc": "Deep + budget"},
    {"name": "deep_fast", "args": ["--deep", "--fast"], "desc": "Deep + fast"},
    {"name": "single_claude", "args": ["--model", "claude"], "desc": "Claude solo"},
    {"name": "single_claude_rigor", "args": ["--model", "claude", "--rigor"], "desc": "Claude + rigor"},
    {"name": "single_gpt", "args": ["--model", "gpt"], "desc": "GPT solo"},
    {"name": "single_gpt_rigor", "args": ["--model", "gpt", "--rigor"], "desc": "GPT + rigor"},
]


@dataclass
class Result:
    mode: str
    question_id: str
    success: bool
    time_seconds: float
    cost_usd: float
    response: str = ""
    scores: dict = field(default_factory=dict)
    error: Optional[str] = None


def extract_cost(output: str) -> float:
    match = re.search(r'[Cc]ost:\s*\$?([\d.]+)', output)
    return float(match.group(1)) if match else 0.0


def extract_response(output: str) -> str:
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


def run_mode(mode: dict, question: str, timeout: int = 300) -> Result:
    cmd = ["minds", "ask", "-y"] + mode["args"] + [question]
    start = time.time()
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        elapsed = time.time() - start
        output = result.stdout + result.stderr
        success = result.returncode == 0
        return Result(
            mode=mode["name"],
            question_id="",
            success=success,
            time_seconds=round(elapsed, 2),
            cost_usd=extract_cost(output),
            response=extract_response(result.stdout)[:2000] if success else "",
            error=None if success else output[:300]
        )
    except subprocess.TimeoutExpired:
        return Result(mode=mode["name"], question_id="", success=False,
                     time_seconds=round(time.time() - start, 2), cost_usd=0, error="Timeout")
    except Exception as e:
        return Result(mode=mode["name"], question_id="", success=False,
                     time_seconds=round(time.time() - start, 2), cost_usd=0, error=str(e))


def judge_response(response: str, question: str) -> dict:
    prompt = f"""Rate 0-10. Be critical and precise.

Question: {question}

Response:
{response[:3000]}

STYLE (0-10): Natural flow, clarity, not over-hedged or over-structured
ADVERSARIAL (0-10): Would survive fact-checking? No fabrication? Honest about uncertainty?
REASONING (0-10): Clear logic? Conclusions supported? Decisive where appropriate?

Output JSON only: {{"style": N, "adversarial": N, "reasoning": N}}"""

    cmd = ["minds", "ask", "--model", "claude", "-y", prompt]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        match = re.search(r'\{[^{}]*"style"[^{}]*\}', result.stdout, re.DOTALL)
        if match:
            return json.loads(re.sub(r'\s+', ' ', match.group()))
    except:
        pass
    return {"style": 5, "adversarial": 5, "reasoning": 5}


def std_dev(vals):
    if len(vals) < 2:
        return 0
    mean = sum(vals) / len(vals)
    return math.sqrt(sum((x - mean) ** 2 for x in vals) / len(vals))


def run_experiment():
    results = []
    total = len(MODE_COMBINATIONS) * len(QUESTIONS)
    count = 0

    for mode in MODE_COMBINATIONS:
        for q in QUESTIONS:
            count += 1
            log.info(f"[{count}/{total}] {mode['name']} x {q['id']}")

            result = run_mode(mode, q["question"])
            result.question_id = q["id"]

            if result.success and result.response:
                log.info(f"  Time: {result.time_seconds}s, Cost: ${result.cost_usd:.4f}")
                result.scores = judge_response(result.response, q["question"])
                avg = sum(result.scores.values()) / 3
                log.info(f"  S:{result.scores['style']} A:{result.scores['adversarial']} R:{result.scores['reasoning']} (avg:{avg:.1f})")
            else:
                log.warning(f"  FAILED: {result.error}")

            results.append(asdict(result))

    return results


def print_full_results(results):
    print("\n" + "=" * 120)
    print("FULL RESULTS BY MODE AND QUESTION")
    print("=" * 120)
    print(f"{'Mode':<20} {'Question':<12} {'Time':>8} {'Cost':>10} {'Style':>7} {'Advers':>7} {'Reason':>7} {'Avg':>7}")
    print("-" * 120)

    for r in results:
        if r["success"] and r.get("scores"):
            s = r["scores"]
            avg = (s["style"] + s["adversarial"] + s["reasoning"]) / 3
            print(f"{r['mode']:<20} {r['question_id']:<12} {r['time_seconds']:>7.1f}s ${r['cost_usd']:>9.4f} {s['style']:>7} {s['adversarial']:>7} {s['reasoning']:>7} {avg:>7.1f}")
        else:
            print(f"{r['mode']:<20} {r['question_id']:<12} {r['time_seconds']:>7.1f}s {'FAILED':>10} {'-':>7} {'-':>7} {'-':>7} {'-':>7}")


def print_summary_with_consistency(results):
    # Group by mode
    by_mode = defaultdict(lambda: {
        'times': [], 'costs': [],
        'style': [], 'adv': [], 'reas': [], 'overall': [],
        'by_question': defaultdict(dict)
    })

    for r in results:
        m = r["mode"]
        if r["success"] and r.get("scores"):
            by_mode[m]['times'].append(r["time_seconds"])
            by_mode[m]['costs'].append(r["cost_usd"])
            s = r["scores"]
            by_mode[m]['style'].append(s["style"])
            by_mode[m]['adv'].append(s["adversarial"])
            by_mode[m]['reas'].append(s["reasoning"])
            avg = (s["style"] + s["adversarial"] + s["reasoning"]) / 3
            by_mode[m]['overall'].append(avg)
            by_mode[m]['by_question'][r["question_id"]] = s

    print("\n" + "=" * 140)
    print("SUMMARY WITH CONSISTENCY (Mean ± StdDev)")
    print("=" * 140)
    print(f"{'Mode':<20} {'Time':>12} {'Cost':>12} {'Style':>12} {'Adversarial':>14} {'Reasoning':>14} {'Overall':>14} {'Consist':>8}")
    print("-" * 140)

    mode_stats = []
    for mode_cfg in MODE_COMBINATIONS:
        m = mode_cfg["name"]
        d = by_mode[m]
        if not d['overall']:
            continue

        avg_t = sum(d['times']) / len(d['times'])
        avg_c = sum(d['costs']) / len(d['costs'])
        avg_s = sum(d['style']) / len(d['style'])
        avg_a = sum(d['adv']) / len(d['adv'])
        avg_r = sum(d['reas']) / len(d['reas'])
        avg_o = sum(d['overall']) / len(d['overall'])

        std_s = std_dev(d['style'])
        std_a = std_dev(d['adv'])
        std_r = std_dev(d['reas'])
        std_o = std_dev(d['overall'])

        # Consistency score: inverse of overall std dev (lower std = more consistent)
        consistency = 10 - (std_o * 3)  # Scale to ~0-10
        consistency = max(0, min(10, consistency))

        mode_stats.append({
            'name': m,
            'avg_time': avg_t,
            'avg_cost': avg_c,
            'avg_style': avg_s,
            'avg_adv': avg_a,
            'avg_reas': avg_r,
            'avg_overall': avg_o,
            'std_overall': std_o,
            'consistency': consistency
        })

        print(f"{m:<20} {avg_t:>6.1f}s      ${avg_c:>9.4f} {avg_s:>5.1f}±{std_s:<4.1f} {avg_a:>7.1f}±{std_a:<4.1f} {avg_r:>7.1f}±{std_r:<4.1f} {avg_o:>7.2f}±{std_o:<4.2f} {consistency:>7.1f}")

    print("=" * 140)

    # Score breakdown by question type
    print("\n" + "=" * 100)
    print("ADVERSARIAL SCORES BY QUESTION TYPE")
    print("=" * 100)
    print(f"{'Mode':<20} {'Fabrication':>12} {'Factual':>12} {'Contested':>12} {'Avg':>10} {'Range':>10}")
    print("-" * 100)

    for mode_cfg in MODE_COMBINATIONS:
        m = mode_cfg["name"]
        d = by_mode[m]
        if not d['by_question']:
            continue

        fab = d['by_question'].get('fabrication', {}).get('adversarial', '-')
        fact = d['by_question'].get('factual', {}).get('adversarial', '-')
        cont = d['by_question'].get('contested', {}).get('adversarial', '-')

        if isinstance(fab, int) and isinstance(fact, int) and isinstance(cont, int):
            avg = (fab + fact + cont) / 3
            rng = max(fab, fact, cont) - min(fab, fact, cont)
            print(f"{m:<20} {fab:>12} {fact:>12} {cont:>12} {avg:>10.1f} {rng:>10}")
        else:
            print(f"{m:<20} {fab:>12} {fact:>12} {cont:>12} {'-':>10} {'-':>10}")

    print("=" * 100)

    # Rankings
    print("\n" + "=" * 80)
    print("RANKINGS")
    print("=" * 80)

    if mode_stats:
        # Best adversarial
        by_adv = sorted(mode_stats, key=lambda x: x['avg_adv'], reverse=True)
        print(f"\nBest Adversarial Resistance:")
        for i, m in enumerate(by_adv[:5], 1):
            print(f"  {i}. {m['name']:<20} {m['avg_adv']:.1f}")

        # Most consistent
        by_consist = sorted(mode_stats, key=lambda x: x['std_overall'])
        print(f"\nMost Consistent (lowest std dev):")
        for i, m in enumerate(by_consist[:5], 1):
            print(f"  {i}. {m['name']:<20} ±{m['std_overall']:.2f}")

        # Best overall
        by_overall = sorted(mode_stats, key=lambda x: x['avg_overall'], reverse=True)
        print(f"\nBest Overall Quality:")
        for i, m in enumerate(by_overall[:5], 1):
            print(f"  {i}. {m['name']:<20} {m['avg_overall']:.2f}")

        # Best cost efficiency (quality per dollar)
        with_cost = [m for m in mode_stats if m['avg_cost'] > 0]
        if with_cost:
            by_eff = sorted(with_cost, key=lambda x: x['avg_overall'] / x['avg_cost'], reverse=True)
            print(f"\nBest Cost Efficiency (quality/cost):")
            for i, m in enumerate(by_eff[:5], 1):
                eff = m['avg_overall'] / m['avg_cost']
                print(f"  {i}. {m['name']:<20} {eff:.0f} (${m['avg_cost']:.4f} for {m['avg_overall']:.1f})")

        # Fastest
        by_speed = sorted(mode_stats, key=lambda x: x['avg_time'])
        print(f"\nFastest:")
        for i, m in enumerate(by_speed[:5], 1):
            print(f"  {i}. {m['name']:<20} {m['avg_time']:.1f}s")


def main():
    log.info("Starting full mode combinations experiment...")
    log.info(f"Testing {len(MODE_COMBINATIONS)} modes x {len(QUESTIONS)} questions = {len(MODE_COMBINATIONS) * len(QUESTIONS)} runs")

    results = run_experiment()

    # Save
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"/home/keeva/socrates/experiments/mode_combinations_{timestamp}.json"
    with open(output_file, 'w') as f:
        json.dump({
            "timestamp": timestamp,
            "questions": QUESTIONS,
            "modes": MODE_COMBINATIONS,
            "results": results
        }, f, indent=2)
    log.info(f"\nResults saved to: {output_file}")

    print_full_results(results)
    print_summary_with_consistency(results)


if __name__ == "__main__":
    main()

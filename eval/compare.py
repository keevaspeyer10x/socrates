"""Statistical comparison functions for evaluation runs.

Implements Wilson score confidence intervals and McNemar's test
for comparing solver performance with statistical rigor.
"""

import math
from typing import Optional
from scipy import stats


def wilson_score_interval(
    passed: int,
    total: int,
    confidence: float = 0.95
) -> tuple[float, float]:
    """Calculate Wilson score confidence interval for pass rate.

    The Wilson score interval provides better coverage properties than
    the normal approximation, especially for extreme proportions or
    small samples.

    Args:
        passed: Number of passed samples
        total: Total number of samples
        confidence: Confidence level (default 0.95 for 95% CI)

    Returns:
        Tuple of (lower_bound, upper_bound)
    """
    if total == 0:
        return (0.0, 1.0)

    p = passed / total
    n = total

    # Z-score for the confidence level
    z = stats.norm.ppf(1 - (1 - confidence) / 2)
    z2 = z * z

    # Wilson score interval formula
    denominator = 1 + z2 / n
    center = (p + z2 / (2 * n)) / denominator
    margin = z * math.sqrt((p * (1 - p) + z2 / (4 * n)) / n) / denominator

    lower = max(0.0, center - margin)
    upper = min(1.0, center + margin)

    return (lower, upper)


def mcnemar_test(
    run_a_results: list[bool],
    run_b_results: list[bool]
) -> dict:
    """Perform McNemar's test for paired comparison.

    McNemar's test determines if there's a significant difference
    between two classifiers on the same samples. It only considers
    the discordant pairs (where the two methods disagree).

    Args:
        run_a_results: List of pass/fail results for run A
        run_b_results: List of pass/fail results for run B

    Returns:
        Dict with p_value, significant, n_a_better, n_b_better, contingency
    """
    if len(run_a_results) != len(run_b_results):
        raise ValueError("Result lists must have same length")

    # Build contingency table
    # b = A passes, B fails (A better)
    # c = A fails, B passes (B better)
    n_a_better = 0  # A passed, B failed
    n_b_better = 0  # A failed, B passed
    n_both_pass = 0
    n_both_fail = 0

    for a, b in zip(run_a_results, run_b_results):
        if a and not b:
            n_a_better += 1
        elif not a and b:
            n_b_better += 1
        elif a and b:
            n_both_pass += 1
        else:
            n_both_fail += 1

    # If no discordant pairs, return p_value of 1.0
    if n_a_better + n_b_better == 0:
        return {
            "p_value": 1.0,
            "significant": False,
            "n_a_better": n_a_better,
            "n_b_better": n_b_better,
            "contingency": {
                "both_pass": n_both_pass,
                "both_fail": n_both_fail,
                "a_only": n_a_better,
                "b_only": n_b_better,
            }
        }

    # McNemar's test using exact binomial test
    # Under null hypothesis, n_a_better ~ Binomial(n_a_better + n_b_better, 0.5)
    total_discordant = n_a_better + n_b_better
    p_value = stats.binom_test(
        min(n_a_better, n_b_better),
        total_discordant,
        0.5,
        alternative='two-sided'
    ) if hasattr(stats, 'binom_test') else stats.binomtest(
        min(n_a_better, n_b_better),
        total_discordant,
        0.5,
        alternative='two-sided'
    ).pvalue

    return {
        "p_value": float(p_value),
        "significant": p_value < 0.05,
        "n_a_better": n_a_better,
        "n_b_better": n_b_better,
        "contingency": {
            "both_pass": n_both_pass,
            "both_fail": n_both_fail,
            "a_only": n_a_better,
            "b_only": n_b_better,
        }
    }


def classify_failure(
    passed: bool,
    error: Optional[str],
    score: float
) -> Optional[str]:
    """Classify the failure mode of a sample.

    Failure modes:
    - wrong_answer: Model produced incorrect output
    - timeout: Exceeded time limit
    - crash: Unexpected error
    - cost_limit: Exceeded token/cost budget

    Args:
        passed: Whether the sample passed
        error: Error message if any
        score: Score value

    Returns:
        Failure mode string or None if passed
    """
    if passed:
        return None

    if error:
        error_lower = error.lower()
        if "timeout" in error_lower:
            return "timeout"
        if "cost" in error_lower or "budget" in error_lower:
            return "cost_limit"
        # Any other error is a crash
        return "crash"

    # No error but didn't pass = wrong answer
    return "wrong_answer"


def compare_runs(
    run_a,  # RunSummary
    run_b,  # RunSummary
    episodes_a: list[dict],
    episodes_b: list[dict]
) -> dict:
    """Compare two evaluation runs with statistical analysis.

    Args:
        run_a: Summary for first run
        run_b: Summary for second run
        episodes_a: Episode data for first run
        episodes_b: Episode data for second run

    Returns:
        Comparison results including CI and McNemar test
    """
    # Calculate Wilson CIs
    wilson_a = wilson_score_interval(run_a.passed, run_a.total_samples)
    wilson_b = wilson_score_interval(run_b.passed, run_b.total_samples)

    # Match samples by ID for McNemar test
    samples_a = {e["sample_id"]: e.get("passed", e.get("outcome", {}).get("passed", False)) for e in episodes_a}
    samples_b = {e["sample_id"]: e.get("passed", e.get("outcome", {}).get("passed", False)) for e in episodes_b}

    # Get common samples
    common_ids = set(samples_a.keys()) & set(samples_b.keys())

    if common_ids:
        results_a = [samples_a[sid] for sid in sorted(common_ids)]
        results_b = [samples_b[sid] for sid in sorted(common_ids)]
        mcnemar_result = mcnemar_test(results_a, results_b)
    else:
        mcnemar_result = {
            "p_value": None,
            "significant": None,
            "n_a_better": 0,
            "n_b_better": 0,
            "note": "No common samples for paired comparison"
        }

    # Cost efficiency
    cost_efficiency = {
        "run_a_cost_per_sample": run_a.total_cost_usd / run_a.total_samples if run_a.total_samples > 0 else 0,
        "run_b_cost_per_sample": run_b.total_cost_usd / run_b.total_samples if run_b.total_samples > 0 else 0,
        "run_a_cost_per_success": run_a.cost_per_success,
        "run_b_cost_per_success": run_b.cost_per_success,
    }

    return {
        "run_a": {
            "run_id": run_a.run_id,
            "solver": run_a.solver,
            "pass_rate": run_a.pass_rate,
            "passed": run_a.passed,
            "total": run_a.total_samples,
        },
        "run_b": {
            "run_id": run_b.run_id,
            "solver": run_b.solver,
            "pass_rate": run_b.pass_rate,
            "passed": run_b.passed,
            "total": run_b.total_samples,
        },
        "wilson_ci_a": wilson_a,
        "wilson_ci_b": wilson_b,
        "mcnemar": mcnemar_result,
        "cost_efficiency": cost_efficiency,
        "common_samples": len(common_ids),
    }


def analyze_failures(episodes: list[dict]) -> dict:
    """Analyze failure modes in a set of episodes.

    Args:
        episodes: List of episode data

    Returns:
        Failure taxonomy breakdown
    """
    taxonomy = {
        "wrong_answer": 0,
        "timeout": 0,
        "crash": 0,
        "cost_limit": 0,
        "unknown": 0,
    }

    for episode in episodes:
        outcome = episode.get("outcome", {})
        passed = outcome.get("passed", False)

        if passed:
            continue

        error = outcome.get("error_message", None)
        failure_mode = outcome.get("failure_mode") or classify_failure(
            passed=False,
            error=error,
            score=outcome.get("score", 0.0)
        )

        if failure_mode in taxonomy:
            taxonomy[failure_mode] += 1
        else:
            taxonomy["unknown"] += 1

    return taxonomy

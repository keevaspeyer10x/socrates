"""Tests for eval/compare.py - Statistical comparison functions."""

import pytest
import math


class TestWilsonCI:
    """Tests for Wilson score confidence interval."""

    def test_normal_case(self):
        """Wilson CI should calculate correct bounds for typical case."""
        from eval.compare import wilson_score_interval

        lower, upper = wilson_score_interval(passed=75, total=100, confidence=0.95)

        # Expected approximately (0.66, 0.83) for 75/100
        assert 0.65 < lower < 0.67
        assert 0.82 < upper < 0.84

    def test_all_pass(self):
        """Wilson CI for 100% pass rate should have upper bound of 1.0."""
        from eval.compare import wilson_score_interval

        lower, upper = wilson_score_interval(passed=100, total=100, confidence=0.95)

        assert upper == 1.0
        assert lower < 1.0  # Lower bound should be less than 1.0
        assert lower > 0.95  # But still high

    def test_all_fail(self):
        """Wilson CI for 0% pass rate should have lower bound of 0.0."""
        from eval.compare import wilson_score_interval

        lower, upper = wilson_score_interval(passed=0, total=100, confidence=0.95)

        assert lower < 0.001  # Effectively 0 (floating point)
        assert upper > 0.0  # Upper bound should be greater than 0.0
        assert upper < 0.05  # But still low

    def test_small_sample(self):
        """Wilson CI should have wider bounds for small samples."""
        from eval.compare import wilson_score_interval

        small_lower, small_upper = wilson_score_interval(passed=2, total=5, confidence=0.95)
        large_lower, large_upper = wilson_score_interval(passed=40, total=100, confidence=0.95)

        # Small sample should have wider CI
        small_width = small_upper - small_lower
        large_width = large_upper - large_lower
        assert small_width > large_width

    def test_edge_case_zero_total(self):
        """Wilson CI should handle zero total samples."""
        from eval.compare import wilson_score_interval

        lower, upper = wilson_score_interval(passed=0, total=0, confidence=0.95)

        # Should return some default (e.g., 0.0, 1.0 or NaN handling)
        assert lower >= 0.0
        assert upper <= 1.0


class TestMcNemar:
    """Tests for McNemar's test."""

    def test_significant_difference(self):
        """McNemar should detect significant difference when one method is better."""
        from eval.compare import mcnemar_test

        # A passes on 80 samples that B fails, B passes on 20 that A fails
        # This is a significant difference
        run_a = [True] * 80 + [False] * 20 + [True] * 50 + [False] * 50
        run_b = [False] * 80 + [True] * 20 + [True] * 50 + [False] * 50

        result = mcnemar_test(run_a, run_b)

        assert result["p_value"] < 0.05
        assert result["significant"] == True  # Use == for numpy bool compatibility

    def test_no_difference(self):
        """McNemar should not detect significance when methods are similar."""
        from eval.compare import mcnemar_test

        # Similar number of discordant pairs
        run_a = [True] * 50 + [False] * 50 + [True] * 50 + [False] * 50
        run_b = [False] * 50 + [True] * 50 + [True] * 50 + [False] * 50

        result = mcnemar_test(run_a, run_b)

        assert result["p_value"] > 0.05
        assert result["significant"] is False

    def test_identical_results(self):
        """McNemar should return p_value=1.0 for identical results."""
        from eval.compare import mcnemar_test

        run_a = [True, False, True, True, False]
        run_b = [True, False, True, True, False]  # Identical

        result = mcnemar_test(run_a, run_b)

        assert result["p_value"] == 1.0
        assert result["significant"] is False

    def test_contingency_table(self):
        """McNemar should return contingency table values."""
        from eval.compare import mcnemar_test

        # A wins on 3, B wins on 1, both pass on 2, both fail on 1
        run_a = [True, True, True, False, True, True, False]
        run_b = [False, False, False, True, True, True, False]

        result = mcnemar_test(run_a, run_b)

        assert "n_a_better" in result  # Cases where A passed, B failed
        assert "n_b_better" in result  # Cases where B passed, A failed


class TestFailureTaxonomy:
    """Tests for failure classification."""

    def test_classify_wrong_answer(self):
        """Should classify incorrect output as wrong_answer."""
        from eval.compare import classify_failure

        failure_mode = classify_failure(
            passed=False,
            error=None,
            score=0.0
        )

        assert failure_mode == "wrong_answer"

    def test_classify_timeout(self):
        """Should classify timeout error correctly."""
        from eval.compare import classify_failure

        failure_mode = classify_failure(
            passed=False,
            error="TimeoutError: Exceeded 300s limit",
            score=0.0
        )

        assert failure_mode == "timeout"

    def test_classify_crash(self):
        """Should classify unexpected error as crash."""
        from eval.compare import classify_failure

        failure_mode = classify_failure(
            passed=False,
            error="RuntimeError: Unexpected exception",
            score=0.0
        )

        assert failure_mode == "crash"

    def test_classify_cost_limit(self):
        """Should classify cost/budget errors."""
        from eval.compare import classify_failure

        failure_mode = classify_failure(
            passed=False,
            error="Budget exceeded: cost limit reached",
            score=0.0
        )

        assert failure_mode == "cost_limit"

    def test_classify_passed(self):
        """Should return None for passed samples."""
        from eval.compare import classify_failure

        failure_mode = classify_failure(
            passed=True,
            error=None,
            score=1.0
        )

        assert failure_mode is None


class TestCompareRuns:
    """Tests for compare_runs function."""

    def test_compare_runs_basic(self):
        """compare_runs should return comparison statistics."""
        from eval.compare import compare_runs
        from eval.state import RunSummary

        run_a = RunSummary(
            run_id="run_a",
            benchmark="gsm8k",
            solver="baseline",
            total_samples=100,
            passed=70,
            failed=30,
            pass_rate=0.7,
            total_cost_usd=1.0
        )

        run_b = RunSummary(
            run_id="run_b",
            benchmark="gsm8k",
            solver="minds",
            total_samples=100,
            passed=80,
            failed=20,
            pass_rate=0.8,
            total_cost_usd=5.0
        )

        # Mock episodes with matching sample IDs
        episodes_a = [{"sample_id": f"s{i}", "passed": i < 70} for i in range(100)]
        episodes_b = [{"sample_id": f"s{i}", "passed": i < 80} for i in range(100)]

        result = compare_runs(run_a, run_b, episodes_a, episodes_b)

        assert "run_a" in result
        assert "run_b" in result
        assert "wilson_ci_a" in result
        assert "wilson_ci_b" in result
        assert "mcnemar" in result
        assert "cost_efficiency" in result

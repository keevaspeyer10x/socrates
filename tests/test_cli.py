"""Tests for eval/cli.py - CLI commands and benchmark task creation."""

import pytest
from unittest.mock import patch, MagicMock
import sys


class TestGetBenchmarkTask:
    """Tests for _get_benchmark_task function."""

    @pytest.fixture(autouse=True)
    def mock_inspect_evals(self):
        """Mock inspect_evals module for tests."""
        # Create mock modules
        mock_gsm8k = MagicMock()
        mock_gsm8k.gsm8k = MagicMock(return_value="gsm8k_task")

        mock_mmlu = MagicMock()
        mock_mmlu.mmlu = MagicMock(return_value="mmlu_task")

        mock_humaneval = MagicMock()
        mock_humaneval.humaneval = MagicMock(return_value="humaneval_task")

        mock_mbpp = MagicMock()
        mock_mbpp.mbpp = MagicMock(return_value="mbpp_task")

        mock_swe_bench = MagicMock()
        mock_swe_bench.swe_bench = MagicMock(return_value="swe_bench_task")

        # Patch sys.modules
        with patch.dict(sys.modules, {
            'inspect_evals': MagicMock(),
            'inspect_evals.gsm8k': mock_gsm8k,
            'inspect_evals.mmlu': mock_mmlu,
            'inspect_evals.humaneval': mock_humaneval,
            'inspect_evals.mbpp': mock_mbpp,
            'inspect_evals.swe_bench': mock_swe_bench,
        }):
            yield

    def test_gsm8k_returns_task(self):
        """gsm8k benchmark should return a valid task."""
        from eval.cli import _get_benchmark_task

        task = _get_benchmark_task("gsm8k")
        assert task is not None

    def test_mmlu_returns_task(self):
        """mmlu benchmark should return a valid task."""
        from eval.cli import _get_benchmark_task

        task = _get_benchmark_task("mmlu")
        assert task is not None

    def test_humaneval_returns_task(self):
        """humaneval benchmark should return a valid task."""
        from eval.cli import _get_benchmark_task

        task = _get_benchmark_task("humaneval")
        assert task is not None

    def test_humaneval_fast_returns_task(self):
        """humaneval_fast benchmark should return a valid task with 1 epoch."""
        from eval.cli import _get_benchmark_task

        task = _get_benchmark_task("humaneval_fast")
        assert task is not None

    def test_mbpp_returns_task(self):
        """mbpp benchmark should return a valid task."""
        from eval.cli import _get_benchmark_task

        task = _get_benchmark_task("mbpp")
        assert task is not None

    def test_benchmark_name_normalization(self):
        """Benchmark names should be normalized (case-insensitive, hyphen to underscore)."""
        from eval.cli import _get_benchmark_task

        # These should all work
        task1 = _get_benchmark_task("HumanEval")
        task2 = _get_benchmark_task("human-eval")
        task3 = _get_benchmark_task("HUMANEVAL")

        assert task1 is not None
        assert task2 is not None
        assert task3 is not None

    def test_unknown_benchmark_raises(self):
        """Unknown benchmark should raise ValueError."""
        from eval.cli import _get_benchmark_task

        with pytest.raises(ValueError, match="Unknown benchmark"):
            _get_benchmark_task("nonexistent_benchmark")

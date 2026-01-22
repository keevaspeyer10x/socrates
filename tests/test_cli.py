"""Tests for eval/cli.py - CLI commands and benchmark task creation."""

import pytest
from unittest.mock import patch, MagicMock
import sys


class TestGetBenchmarkTask:
    """Tests for _get_benchmark_task function."""

    @pytest.fixture(autouse=True)
    def mock_inspect_evals(self):
        """Mock inspect_evals module for tests."""
        # Create mock modules with MagicMock return values that support attribute setting
        mock_gsm8k = MagicMock()
        mock_gsm8k.gsm8k = MagicMock(return_value=MagicMock(name="gsm8k_task"))

        mock_mmlu = MagicMock()
        mock_mmlu.mmlu = MagicMock(return_value=MagicMock(name="mmlu_task"))

        mock_humaneval = MagicMock()
        mock_humaneval.humaneval = MagicMock(return_value=MagicMock(name="humaneval_task"))

        mock_mbpp = MagicMock()
        mock_mbpp.mbpp = MagicMock(return_value=MagicMock(name="mbpp_task"))

        mock_swe_bench = MagicMock()
        mock_swe_bench.swe_bench = MagicMock(return_value=MagicMock(name="swe_bench_task"))

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
        assert task.epochs == 5  # Should be set to 5 for standard benchmarking

    def test_humaneval_fast_returns_task(self):
        """humaneval_fast benchmark should return a valid task with 1 epoch."""
        from eval.cli import _get_benchmark_task

        task = _get_benchmark_task("humaneval_fast")
        assert task is not None
        assert task.epochs == 1  # Fast mode should have 1 epoch

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


class TestBigCodeBench:
    """Tests for BigCodeBench benchmark support."""

    @pytest.fixture(autouse=True)
    def mock_bigcodebench(self):
        """Mock bigcodebench module for tests."""
        mock_bigcodebench_mod = MagicMock()
        mock_task = MagicMock(name="bigcodebench_task")
        mock_task.sandbox = ("docker", "compose.yaml")
        mock_bigcodebench_mod.bigcodebench = MagicMock(return_value=mock_task)

        with patch.dict(sys.modules, {
            'inspect_evals': MagicMock(),
            'inspect_evals.bigcodebench': mock_bigcodebench_mod,
        }):
            yield mock_bigcodebench_mod

    def test_bigcodebench_returns_task(self, mock_bigcodebench):
        """bigcodebench benchmark should return a valid task."""
        from eval.cli import _get_benchmark_task

        task = _get_benchmark_task("bigcodebench")
        assert task is not None
        mock_bigcodebench.bigcodebench.assert_called_once()

    @pytest.mark.integration
    def test_bigcodebench_hard_returns_task(self):
        """bigcodebench_hard benchmark should return a valid task with hard subset.

        This is an integration test because bigcodebench_hard:
        1. Loads dataset from HuggingFace (requires network)
        2. Sets up Docker compose (requires Docker)
        3. Has complex internal imports that are hard to mock

        Run with: pytest -m integration
        """
        pytest.skip("Integration test - requires network and Docker. Run with: pytest -m integration")


class TestAnalyzeFailures:
    """Tests for analyze-failures command."""

    @pytest.fixture
    def mock_run_dir(self, tmp_path):
        """Create a mock run directory with episodes."""
        run_dir = tmp_path / "eval_logs" / "runs" / "test_run_123"
        run_dir.mkdir(parents=True)

        # Create summary
        import json
        summary = {
            "run_id": "test_run_123",
            "benchmark": "bigcodebench",
            "solver": "baseline",
            "total_samples": 5,
            "passed": 2,
            "failed": 3,
            "pass_rate": 0.4,
            "total_cost_usd": 0.05
        }
        (run_dir / "summary.json").write_text(json.dumps(summary))

        # Create episodes
        episodes_dir = run_dir / "episodes"
        episodes_dir.mkdir()

        # 2 passed, 3 failed
        episodes = [
            {"sample_id": 1, "outcome": {"passed": True}},
            {"sample_id": 2, "outcome": {"passed": False}},
            {"sample_id": 3, "outcome": {"passed": True}},
            {"sample_id": 4, "outcome": {"passed": False}},
            {"sample_id": 5, "outcome": {"passed": False}},
        ]
        for ep in episodes:
            (episodes_dir / f"{ep['sample_id']}.json").write_text(json.dumps(ep))

        return tmp_path

    @pytest.fixture
    def mock_run_dir_2(self, tmp_path):
        """Create a second mock run directory with different failures."""
        run_dir = tmp_path / "eval_logs" / "runs" / "test_run_456"
        run_dir.mkdir(parents=True)

        import json
        summary = {
            "run_id": "test_run_456",
            "benchmark": "bigcodebench",
            "solver": "minds",
            "total_samples": 5,
            "passed": 3,
            "failed": 2,
            "pass_rate": 0.6,
            "total_cost_usd": 0.10
        }
        (run_dir / "summary.json").write_text(json.dumps(summary))

        episodes_dir = run_dir / "episodes"
        episodes_dir.mkdir()

        # Different failure pattern: 2, 5 fail (overlap with run 1: 2, 5)
        episodes = [
            {"sample_id": 1, "outcome": {"passed": True}},
            {"sample_id": 2, "outcome": {"passed": False}},  # Also failed in run 1
            {"sample_id": 3, "outcome": {"passed": True}},
            {"sample_id": 4, "outcome": {"passed": True}},   # Passed here, failed in run 1
            {"sample_id": 5, "outcome": {"passed": False}},  # Also failed in run 1
        ]
        for ep in episodes:
            (episodes_dir / f"{ep['sample_id']}.json").write_text(json.dumps(ep))

        return tmp_path

    def test_analyze_failures_extracts_failed_ids(self, mock_run_dir):
        """analyze-failures should extract sample IDs that failed."""
        from click.testing import CliRunner
        from eval.cli import cli
        import json

        runner = CliRunner()
        output_file = mock_run_dir / "fail_set.json"

        with patch('eval.cli.LOGS_DIR', mock_run_dir / "eval_logs"):
            result = runner.invoke(cli, [
                "analyze-failures", "test_run_123",
                "--output", str(output_file)
            ])

        assert result.exit_code == 0, f"Command failed: {result.output}"
        assert output_file.exists()

        fail_set = json.loads(output_file.read_text())
        assert "sample_ids" in fail_set
        assert set(fail_set["sample_ids"]) == {2, 4, 5}  # The failed ones

    def test_analyze_failures_intersection(self, mock_run_dir, mock_run_dir_2):
        """analyze-failures --intersect should find common failures."""
        from click.testing import CliRunner
        from eval.cli import cli
        import json

        # Both fixtures use same tmp_path, so both runs exist
        runner = CliRunner()
        output_file = mock_run_dir / "intersect_fail_set.json"

        with patch('eval.cli.LOGS_DIR', mock_run_dir / "eval_logs"):
            result = runner.invoke(cli, [
                "analyze-failures", "test_run_123", "test_run_456",
                "--intersect",
                "--output", str(output_file)
            ])

        assert result.exit_code == 0, f"Command failed: {result.output}"
        assert output_file.exists()

        fail_set = json.loads(output_file.read_text())
        assert "sample_ids" in fail_set
        assert "mode" in fail_set
        assert fail_set["mode"] == "intersect"
        # Intersection: samples that failed in BOTH runs
        assert set(fail_set["sample_ids"]) == {2, 5}

    def test_analyze_failures_run_not_found(self, tmp_path):
        """analyze-failures should error on non-existent run."""
        from click.testing import CliRunner
        from eval.cli import cli

        runner = CliRunner()

        with patch('eval.cli.LOGS_DIR', tmp_path / "eval_logs"):
            result = runner.invoke(cli, [
                "analyze-failures", "nonexistent_run",
                "--output", str(tmp_path / "out.json")
            ])

        assert result.exit_code != 0
        assert "not found" in result.output.lower()

    def test_analyze_failures_all_passed(self, tmp_path):
        """analyze-failures should handle case where all samples passed."""
        from click.testing import CliRunner
        from eval.cli import cli
        import json

        # Create run where all passed
        run_dir = tmp_path / "eval_logs" / "runs" / "all_pass_run"
        run_dir.mkdir(parents=True)

        summary = {
            "run_id": "all_pass_run",
            "benchmark": "gsm8k",
            "solver": "baseline",
            "total_samples": 3,
            "passed": 3,
            "failed": 0,
            "pass_rate": 1.0,
            "total_cost_usd": 0.01
        }
        (run_dir / "summary.json").write_text(json.dumps(summary))

        episodes_dir = run_dir / "episodes"
        episodes_dir.mkdir()
        for i in range(1, 4):
            (episodes_dir / f"{i}.json").write_text(
                json.dumps({"sample_id": i, "outcome": {"passed": True}})
            )

        runner = CliRunner()
        output_file = tmp_path / "empty_fail_set.json"

        with patch('eval.cli.LOGS_DIR', tmp_path / "eval_logs"):
            result = runner.invoke(cli, [
                "analyze-failures", "all_pass_run",
                "--output", str(output_file)
            ])

        assert result.exit_code == 0
        fail_set = json.loads(output_file.read_text())
        assert fail_set["sample_ids"] == []

    def test_fail_set_json_format(self, mock_run_dir):
        """Fail set JSON should have required fields."""
        from click.testing import CliRunner
        from eval.cli import cli
        import json

        runner = CliRunner()
        output_file = mock_run_dir / "fail_set.json"

        with patch('eval.cli.LOGS_DIR', mock_run_dir / "eval_logs"):
            result = runner.invoke(cli, [
                "analyze-failures", "test_run_123",
                "--output", str(output_file)
            ])

        assert result.exit_code == 0
        fail_set = json.loads(output_file.read_text())

        # Required fields
        assert "source_runs" in fail_set
        assert "sample_ids" in fail_set
        assert isinstance(fail_set["source_runs"], list)
        assert isinstance(fail_set["sample_ids"], list)
        assert "test_run_123" in fail_set["source_runs"]

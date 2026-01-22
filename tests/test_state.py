"""Tests for eval/state.py - State machine and data models."""

import json
import pytest
from pathlib import Path
from datetime import datetime


class TestEvalState:
    """Tests for EvalState workflow state machine."""

    def test_create_default_state(self):
        """Default state should be IDLE."""
        from eval.state import EvalState

        state = EvalState()
        assert state.phase == "IDLE"
        assert state.current_run_id is None

    def test_serialize_to_json(self):
        """State should serialize to valid JSON."""
        from eval.state import EvalState

        state = EvalState()
        json_str = state.to_json()

        parsed = json.loads(json_str)
        assert parsed["phase"] == "IDLE"

    def test_load_from_json(self):
        """State should load from JSON string."""
        from eval.state import EvalState

        json_str = '{"phase": "RUNNING", "current_run_id": "test123"}'
        state = EvalState.from_json(json_str)

        assert state.phase == "RUNNING"
        assert state.current_run_id == "test123"

    def test_update_phase(self):
        """Phase transitions should work correctly."""
        from eval.state import EvalState

        state = EvalState()
        state.start_run("run_001", "gsm8k", "baseline")

        assert state.phase == "RUNNING"
        assert state.current_run_id == "run_001"

    def test_save_and_load_file(self, tmp_path):
        """State should persist to and load from file."""
        from eval.state import EvalState

        state = EvalState()
        state.start_run("run_001", "gsm8k", "baseline")

        path = tmp_path / ".eval_state.json"
        state.save(path)

        loaded = EvalState.load(path)
        assert loaded.phase == "RUNNING"
        assert loaded.current_run_id == "run_001"


class TestEpisode:
    """Tests for Episode data model."""

    def test_create_episode(self):
        """Should create Episode with required fields."""
        from eval.state import Episode

        episode = Episode(
            sample_id="gsm8k_42",
            context={"input": "What is 2+2?", "target": "4"},
            traces=[],
            action={"output": "4"},
            outcome={"passed": True, "score": 1.0},
            cost={"input_tokens": 100, "output_tokens": 50, "usd": 0.001}
        )

        assert episode.sample_id == "gsm8k_42"
        assert episode.outcome["passed"] is True

    def test_episode_to_json(self):
        """Episode should serialize to JSON."""
        from eval.state import Episode

        episode = Episode(
            sample_id="test",
            context={"input": "test"},
            traces=[{"type": "model", "content": "thinking"}],
            action={"output": "result"},
            outcome={"passed": True},
            cost={"usd": 0.01}
        )

        json_str = episode.to_json()
        parsed = json.loads(json_str)

        assert parsed["sample_id"] == "test"
        assert len(parsed["traces"]) == 1

    def test_calculate_cost(self):
        """Should calculate cost from token usage."""
        from eval.state import Episode, calculate_cost

        cost = calculate_cost(
            input_tokens=1000,
            output_tokens=500,
            model="anthropic/claude-sonnet-4-20250514"
        )

        assert "usd" in cost
        assert cost["usd"] > 0


class TestRunConfig:
    """Tests for RunConfig model."""

    def test_create_run_config(self):
        """Should create RunConfig with defaults."""
        from eval.state import RunConfig

        config = RunConfig(
            benchmark="gsm8k",
            solver="baseline",
            model="anthropic/claude-sonnet-4-20250514"
        )

        assert config.benchmark == "gsm8k"
        assert config.samples is None  # Default: all samples


class TestRunSummary:
    """Tests for RunSummary model."""

    def test_create_summary(self):
        """Should create RunSummary with metrics."""
        from eval.state import RunSummary

        summary = RunSummary(
            run_id="run_001",
            benchmark="gsm8k",
            solver="baseline",
            total_samples=10,
            passed=7,
            failed=3,
            pass_rate=0.7,
            total_cost_usd=0.50
        )

        assert summary.pass_rate == 0.7
        assert summary.cost_per_success == pytest.approx(0.50 / 7, rel=0.01)

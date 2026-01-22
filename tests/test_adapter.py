"""Tests for eval/adapters/inspect_adapter.py - Inspect log extraction."""

import pytest
from unittest.mock import MagicMock


class TestInspectAdapter:
    """Tests for extracting episodes from Inspect logs."""

    def test_extract_context(self):
        """Should extract context from EvalSample."""
        from eval.adapters.inspect_adapter import InspectAdapter

        sample = MagicMock()
        sample.input = "What is 2+2?"
        sample.target = "4"
        sample.metadata = {"difficulty": "easy"}

        adapter = InspectAdapter()
        context = adapter.extract_context(sample)

        assert context["input"] == "What is 2+2?"
        assert context["target"] == "4"

    def test_extract_tool_trace(self):
        """Should extract trace from ToolEvent."""
        from eval.adapters.inspect_adapter import InspectAdapter

        tool_event = MagicMock()
        tool_event.function = "calculator"
        tool_event.arguments = {"expression": "2+2"}
        tool_event.result = "4"
        tool_event.working_time = 0.5

        adapter = InspectAdapter()
        trace = adapter.extract_tool_trace(tool_event)

        assert trace["type"] == "tool"
        assert trace["function"] == "calculator"
        assert trace["result"] == "4"

    def test_extract_model_trace(self):
        """Should extract trace from ModelEvent."""
        from eval.adapters.inspect_adapter import InspectAdapter

        model_event = MagicMock()
        model_event.model = "anthropic/claude-sonnet"
        model_event.output = MagicMock()
        model_event.output.completion = "Let me calculate..."
        model_event.working_time = 1.2

        adapter = InspectAdapter()
        trace = adapter.extract_model_trace(model_event)

        assert trace["type"] == "model"
        assert "calculate" in trace["content"]

    def test_map_scores_to_outcome(self):
        """Should map Inspect scores to outcome with pass/fail."""
        from eval.adapters.inspect_adapter import InspectAdapter

        scores = {
            "accuracy": MagicMock(value=1.0),
        }

        adapter = InspectAdapter()
        outcome = adapter.map_outcome(scores, error=None)

        assert outcome["passed"] is True
        assert outcome["score"] == 1.0
        assert outcome["failure_mode"] is None

    def test_map_failure_outcome(self):
        """Should map failed scores to outcome with failure mode."""
        from eval.adapters.inspect_adapter import InspectAdapter

        scores = {
            "accuracy": MagicMock(value=0.0),
        }

        adapter = InspectAdapter()
        outcome = adapter.map_outcome(scores, error=None)

        assert outcome["passed"] is False
        assert outcome["failure_mode"] == "wrong_answer"

    def test_map_error_outcome(self):
        """Should map errors to outcome with failure mode."""
        from eval.adapters.inspect_adapter import InspectAdapter

        # Test timeout error (detected from message)
        error = MagicMock()
        error.message = "Timeout exceeded"

        adapter = InspectAdapter()
        outcome = adapter.map_outcome(scores={}, error=error)

        assert outcome["passed"] is False
        assert outcome["failure_mode"] == "timeout"

        # Test generic error
        error2 = MagicMock()
        error2.message = "Something went wrong"

        outcome2 = adapter.map_outcome(scores={}, error=error2)
        assert outcome2["failure_mode"] == "error"

    def test_calculate_cost_from_usage(self):
        """Should calculate USD cost from model usage."""
        from eval.adapters.inspect_adapter import InspectAdapter

        usage = {
            "anthropic/claude-sonnet-4-20250514": MagicMock(
                input_tokens=1000,
                output_tokens=500
            )
        }

        adapter = InspectAdapter()
        cost = adapter.calculate_cost(usage)

        assert "input_tokens" in cost
        assert "output_tokens" in cost
        assert "usd" in cost
        assert cost["usd"] > 0

    def test_extract_episode_from_sample(self):
        """Should extract complete Episode from EvalSample."""
        from eval.adapters.inspect_adapter import InspectAdapter
        from eval.state import Episode

        sample = MagicMock()
        sample.id = "gsm8k_42"
        sample.input = "What is 2+2?"
        sample.target = "4"
        sample.output = MagicMock(completion="The answer is 4")
        sample.scores = {"accuracy": MagicMock(value=1.0)}
        sample.error = None
        sample.events = []  # No events in simple case
        sample.model_usage = {}
        sample.metadata = {}

        adapter = InspectAdapter()
        episode = adapter.extract_episode(sample, run_id="run_001")

        assert isinstance(episode, Episode)
        assert episode.sample_id == "gsm8k_42"
        assert episode.outcome["passed"] is True

    def test_handle_empty_events(self):
        """Should handle samples with no events gracefully."""
        from eval.adapters.inspect_adapter import InspectAdapter

        sample = MagicMock()
        sample.events = None

        adapter = InspectAdapter()
        traces = adapter.extract_traces(sample)

        assert traces == []

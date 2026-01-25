"""Adapter for extracting episodes from Inspect AI evaluation logs."""

from typing import Any, Optional
from ..state import Episode, calculate_cost


class InspectAdapter:
    """Converts Inspect AI logs to Socrates episode format.

    This adapter extracts the 4-tuple (context, traces, action, outcome)
    from Inspect's EvalSample and event structures.
    """

    def extract_context(self, sample: Any) -> dict:
        """Extract context from EvalSample.

        Context contains the input problem and expected answer.
        """
        return {
            "input": str(sample.input) if sample.input else "",
            "target": sample.target if hasattr(sample, "target") else None,
            "metadata": getattr(sample, "metadata", {}) or {},
        }

    def extract_tool_trace(self, event: Any) -> dict:
        """Extract trace from ToolEvent.

        Tool events capture function calls and their results.
        """
        return {
            "type": "tool",
            "function": getattr(event, "function", "unknown"),
            "arguments": getattr(event, "arguments", {}),
            "result": str(getattr(event, "result", ""))[:1000],  # Truncate
            "duration": getattr(event, "working_time", 0),
        }

    def extract_model_trace(self, event: Any) -> dict:
        """Extract trace from ModelEvent.

        Model events capture LLM responses and reasoning.
        """
        content = ""
        if hasattr(event, "output") and event.output:
            content = getattr(event.output, "completion", "")
        elif hasattr(event, "content"):
            content = event.content

        return {
            "type": "model",
            "model": getattr(event, "model", "unknown"),
            "content": str(content)[:2000],  # Truncate for storage
            "duration": getattr(event, "working_time", 0),
        }

    def extract_traces(self, sample: Any) -> list[dict]:
        """Extract all traces from sample events.

        Events are ordered chronologically and contain both
        model responses and tool calls.
        """
        events = getattr(sample, "events", None)
        if not events:
            return []

        traces = []
        for event in events:
            event_type = getattr(event, "event", None)

            if event_type == "tool":
                traces.append(self.extract_tool_trace(event))
            elif event_type == "model":
                traces.append(self.extract_model_trace(event))
            # Skip other event types (state, span, etc.)

        return traces

    def map_outcome(
        self,
        scores: Optional[dict],
        error: Optional[Any]
    ) -> dict:
        """Map Inspect scores to outcome with failure taxonomy.

        Failure modes:
        - wrong_answer: Model produced incorrect output
        - timeout: Exceeded time limit
        - crash: Unexpected error
        - cost_limit: Exceeded token budget
        - error: Other errors
        """
        if error:
            error_msg = str(getattr(error, "message", str(error))).lower()
            if "timeout" in error_msg:
                failure_mode = "timeout"
            elif "cost" in error_msg or "budget" in error_msg:
                failure_mode = "cost_limit"
            else:
                failure_mode = "error"

            return {
                "passed": False,
                "score": 0.0,
                "failure_mode": failure_mode,
                "error_message": str(error)[:500],
            }

        if not scores:
            return {
                "passed": False,
                "score": 0.0,
                "failure_mode": "error",
            }

        # Check common score keys (order matters - check specific keys first)
        passed = False
        score_value = 0.0

        # Handle 'choice' scorer (used by GPQA, multiple choice benchmarks)
        # The choice scorer returns:
        #   value = 'C' (CORRECT) or 'I' (INCORRECT)
        #   answer = the letter(s) of the correct answer(s)
        if "choice" in scores:
            score_obj = scores["choice"]
            value = getattr(score_obj, "value", None)
            # 'C' means CORRECT, 'I' means INCORRECT
            if value is not None:
                passed = str(value).strip().upper() == 'C'
                score_value = 1.0 if passed else 0.0
            else:
                passed = False
                score_value = 0.0
        else:
            # Check other common score keys
            for key in ["match", "accuracy", "correct", "pass", "resolved", "verify"]:
                if key in scores:
                    score_obj = scores[key]
                    value = getattr(score_obj, "value", score_obj)

                    # Handle letter grades (C=Correct, I=Incorrect, P=Partial)
                    if isinstance(value, str):
                        value_upper = value.upper()
                        if value_upper in ("C", "CORRECT", "Y", "YES", "TRUE", "1"):
                            passed = True
                            score_value = 1.0
                        elif value_upper in ("P", "PARTIAL"):
                            passed = False
                            score_value = 0.5
                        else:
                            passed = False
                            score_value = 0.0
                    else:
                        # Numeric score
                        score_value = float(value) if value is not None else 0.0
                        passed = score_value > 0.5
                    break

        failure_mode = None if passed else "wrong_answer"

        return {
            "passed": passed,
            "score": score_value,
            "failure_mode": failure_mode,
        }

    def calculate_cost(self, model_usage: Optional[dict]) -> dict:
        """Calculate cost from model usage statistics."""
        if not model_usage:
            return {"input_tokens": 0, "output_tokens": 0, "usd": 0.0}

        total_input = 0
        total_output = 0

        for model, usage in model_usage.items():
            total_input += getattr(usage, "input_tokens", 0)
            total_output += getattr(usage, "output_tokens", 0)

        # Use first model for pricing (most common case)
        model = next(iter(model_usage.keys()), "default")
        return calculate_cost(total_input, total_output, model)

    def extract_episode(self, sample: Any, run_id: str) -> Episode:
        """Extract complete Episode from EvalSample.

        This is the main entry point for converting Inspect logs
        to Socrates format.
        """
        # Extract output
        output = ""
        if hasattr(sample, "output") and sample.output:
            output = getattr(sample.output, "completion", "")

        # Count tool calls from traces
        traces = self.extract_traces(sample)
        tool_call_count = sum(1 for t in traces if t["type"] == "tool")

        return Episode(
            sample_id=str(sample.id),
            run_id=run_id,
            context=self.extract_context(sample),
            traces=traces,
            action={
                "output": str(output)[:5000],
                "tool_calls_count": tool_call_count,
            },
            outcome=self.map_outcome(
                getattr(sample, "scores", None),
                getattr(sample, "error", None)
            ),
            cost=self.calculate_cost(getattr(sample, "model_usage", None)),
        )

    def extract_episodes(self, eval_log: Any, run_id: str) -> list[Episode]:
        """Extract all episodes from an evaluation log."""
        samples = getattr(eval_log, "samples", [])
        if not samples:
            return []

        return [
            self.extract_episode(sample, run_id)
            for sample in samples
        ]

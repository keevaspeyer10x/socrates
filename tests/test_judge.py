"""Tests for eval/judge - LLM-as-Judge evaluation system."""

import sys
import pytest
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch


class TestRubric:
    """Tests for rubric loading and validation."""

    def test_criterion_format_anchors(self):
        """Criterion should format anchors correctly."""
        from eval.judge.rubric import Criterion

        criterion = Criterion(
            name="depth",
            description="Test criterion",
            weight=0.25,
            anchors={1: "Low", 3: "Medium", 5: "High"},
        )

        formatted = criterion.format_anchors()
        assert "1: Low" in formatted
        assert "3: Medium" in formatted
        assert "5: High" in formatted

    def test_rubric_normalizes_weights(self):
        """Rubric should normalize weights if they don't sum to 1.0."""
        from eval.judge.rubric import Rubric, Criterion

        criteria = [
            Criterion(name="a", description="A", weight=0.5),
            Criterion(name="b", description="B", weight=0.5),
            Criterion(name="c", description="C", weight=0.5),
        ]
        # Total = 1.5, should be normalized

        rubric = Rubric(
            name="test",
            version="1.0.0",
            description="Test rubric",
            criteria=criteria,
        )

        # Weights should now sum to 1.0
        total_weight = sum(c.weight for c in rubric.criteria)
        assert abs(total_weight - 1.0) < 0.01

    def test_rubric_format_for_prompt(self):
        """Rubric should format correctly for inclusion in prompt."""
        from eval.judge.rubric import Rubric, Criterion

        rubric = Rubric(
            name="test",
            version="1.0.0",
            description="A test rubric",
            criteria=[
                Criterion(name="quality", description="Test quality", weight=1.0),
            ],
            instructions="Be fair.",
        )

        formatted = rubric.format_for_prompt()

        assert "test" in formatted
        assert "1.0.0" in formatted
        assert "A test rubric" in formatted
        assert "quality" in formatted
        assert "Be fair." in formatted

    def test_rubric_to_dict_and_from_dict(self):
        """Rubric should round-trip through dict conversion."""
        from eval.judge.rubric import Rubric, Criterion

        original = Rubric(
            name="test",
            version="1.0.0",
            description="Test rubric",
            criteria=[
                Criterion(
                    name="depth",
                    description="Test depth",
                    weight=0.5,
                    anchors={1: "Low", 5: "High"},
                ),
                Criterion(
                    name="quality",
                    description="Test quality",
                    weight=0.5,
                ),
            ],
            scale_min=1,
            scale_max=5,
            instructions="Test instructions",
        )

        data = original.to_dict()
        restored = Rubric.from_dict(data)

        assert restored.name == original.name
        assert restored.version == original.version
        assert len(restored.criteria) == len(original.criteria)
        assert restored.criteria[0].anchors == original.criteria[0].anchors

    def test_load_rubric_from_yaml(self, tmp_path):
        """Should load rubric from YAML file."""
        from eval.judge.rubric import load_rubric, save_rubric, Rubric, Criterion

        # Create a rubric
        rubric = Rubric(
            name="test_yaml",
            version="1.0.0",
            description="Test YAML loading",
            criteria=[
                Criterion(name="test", description="Test", weight=1.0),
            ],
        )

        # Save to temp file
        rubric_path = tmp_path / "test_rubric.yaml"
        save_rubric(rubric, rubric_path)

        # Load it back
        loaded = load_rubric(rubric_path)

        assert loaded.name == "test_yaml"
        assert loaded.version == "1.0.0"
        assert len(loaded.criteria) == 1

    def test_load_rubric_file_not_found(self):
        """Should raise FileNotFoundError for missing rubric."""
        from eval.judge.rubric import load_rubric

        with pytest.raises(FileNotFoundError):
            load_rubric("/nonexistent/path/rubric.yaml")

    def test_default_reasoning_rubric(self):
        """Default reasoning rubric should have expected criteria."""
        from eval.judge.rubric import DEFAULT_REASONING_RUBRIC

        assert DEFAULT_REASONING_RUBRIC.name == "reasoning"
        criterion_names = [c.name for c in DEFAULT_REASONING_RUBRIC.criteria]
        assert "depth" in criterion_names
        assert "coherence" in criterion_names
        assert "practicality" in criterion_names
        assert "novelty" in criterion_names

    def test_default_debate_rubric(self):
        """Default debate rubric should have expected criteria."""
        from eval.judge.rubric import DEFAULT_DEBATE_RUBRIC

        assert DEFAULT_DEBATE_RUBRIC.name == "debate"
        criterion_names = [c.name for c in DEFAULT_DEBATE_RUBRIC.criteria]
        assert "perspective_coverage" in criterion_names
        assert "synthesis" in criterion_names
        assert "intellectual_honesty" in criterion_names


class TestJudgeScorer:
    """Tests for JudgeScorer."""

    def test_parse_judge_response_with_code_fence(self):
        """Should parse JSON from markdown code fence."""
        from eval.judge.scorer import parse_judge_response

        response = '''Here is my evaluation:

```json
{
  "scores": {
    "depth": {"score": 4, "justification": "Good coverage"}
  },
  "overall_assessment": "Well done",
  "confidence": 0.8
}
```
'''
        parsed = parse_judge_response(response)

        assert parsed is not None
        assert "scores" in parsed
        assert parsed["scores"]["depth"]["score"] == 4

    def test_parse_judge_response_raw_json(self):
        """Should parse raw JSON without code fence."""
        from eval.judge.scorer import parse_judge_response

        response = '{"scores": {"test": {"score": 3}}, "overall_assessment": "OK", "confidence": 0.7}'
        parsed = parse_judge_response(response)

        assert parsed is not None
        assert parsed["confidence"] == 0.7

    def test_parse_judge_response_invalid(self):
        """Should return None for invalid JSON."""
        from eval.judge.scorer import parse_judge_response

        response = "This is not valid JSON at all"
        parsed = parse_judge_response(response)

        assert parsed is None

    def test_calculate_weighted_score(self):
        """Should calculate weighted score correctly."""
        from eval.judge.scorer import calculate_weighted_score
        from eval.judge.rubric import Rubric, Criterion

        rubric = Rubric(
            name="test",
            version="1.0.0",
            description="Test",
            criteria=[
                Criterion(name="a", description="A", weight=0.6),
                Criterion(name="b", description="B", weight=0.4),
            ],
            scale_min=1,
            scale_max=5,
        )

        scores = {
            "a": {"score": 5},  # Max score, normalized to 1.0
            "b": {"score": 1},  # Min score, normalized to 0.0
        }

        weighted = calculate_weighted_score(scores, rubric)

        # Expected: 0.6 * 1.0 + 0.4 * 0.0 = 0.6
        assert abs(weighted - 0.6) < 0.01

    @pytest.mark.asyncio
    async def test_judge_scorer_score(self):
        """JudgeScorer.score should return structured result."""
        from eval.judge.scorer import JudgeScorer

        # Mock inspect_ai.model imports
        mock_chat_system = MagicMock()
        mock_chat_user = MagicMock()

        with patch.dict('sys.modules', {
            'inspect_ai': MagicMock(),
            'inspect_ai.model': MagicMock(
                ChatMessageSystem=mock_chat_system,
                ChatMessageUser=mock_chat_user,
            ),
        }):
            # Mock the model
            mock_model = AsyncMock()
            mock_response = MagicMock()
            mock_response.completion = '''```json
{
  "scores": {
    "depth": {"score": 4, "justification": "Good depth"},
    "coherence": {"score": 3, "justification": "Mostly coherent"},
    "practicality": {"score": 4, "justification": "Practical"},
    "novelty": {"score": 2, "justification": "Standard approach"}
  },
  "overall_assessment": "A solid response",
  "confidence": 0.85
}
```'''
            mock_model.generate = AsyncMock(return_value=mock_response)

            scorer = JudgeScorer()
            scorer._model = mock_model

            result = await scorer.score(
                prompt="How do I optimize a database?",
                response="Use indexes, query optimization, and caching."
            )

            assert "weighted_score" in result
            assert "passed" in result
            assert "scores" in result
            assert result["confidence"] == 0.85
            assert "depth" in result["scores"]


class TestMultiJudge:
    """Tests for MultiJudge ensemble."""

    @pytest.mark.asyncio
    async def test_multi_judge_aggregates_scores(self):
        """MultiJudge should aggregate scores from multiple judges."""
        from eval.judge.ensemble import MultiJudge

        # Create mock judges with predetermined scores
        multi_judge = MultiJudge(
            judge_models=["model1", "model2", "model3"],
            aggregation="median",
        )

        # Mock individual scorers
        mock_results = [
            {"weighted_score": 0.7, "passed": True, "confidence": 0.9},
            {"weighted_score": 0.5, "passed": False, "confidence": 0.8},
            {"weighted_score": 0.8, "passed": True, "confidence": 0.85},
        ]

        for i, judge in enumerate(multi_judge._judges):
            judge.score = AsyncMock(return_value=mock_results[i])

        result = await multi_judge.score(
            prompt="Test prompt",
            response="Test response"
        )

        # Median of [0.5, 0.7, 0.8] = 0.7
        assert abs(result.weighted_score - 0.7) < 0.01
        assert result.passed is True
        assert len(result.individual_scores) == 3

    @pytest.mark.asyncio
    async def test_multi_judge_handles_errors(self):
        """MultiJudge should handle judge errors gracefully."""
        from eval.judge.ensemble import MultiJudge

        multi_judge = MultiJudge(
            judge_models=["model1", "model2"],
        )

        # First judge succeeds, second fails
        multi_judge._judges[0].score = AsyncMock(
            return_value={"weighted_score": 0.8, "passed": True, "confidence": 0.9}
        )
        multi_judge._judges[1].score = AsyncMock(
            side_effect=Exception("API error")
        )

        result = await multi_judge.score(
            prompt="Test prompt",
            response="Test response"
        )

        # Should still produce a result using the successful judge
        assert result.weighted_score == 0.8
        # Should have error in individual scores
        assert any("error" in r for r in result.individual_scores)

    @pytest.mark.asyncio
    async def test_multi_judge_flags_high_variance(self):
        """MultiJudge should flag high variance for human review."""
        from eval.judge.ensemble import MultiJudge

        multi_judge = MultiJudge(
            judge_models=["model1", "model2", "model3"],
            variance_threshold=0.1,
        )

        # Widely varying scores
        mock_results = [
            {"weighted_score": 0.2, "passed": False, "confidence": 0.9},
            {"weighted_score": 0.9, "passed": True, "confidence": 0.9},
            {"weighted_score": 0.5, "passed": False, "confidence": 0.9},
        ]

        for i, judge in enumerate(multi_judge._judges):
            judge.score = AsyncMock(return_value=mock_results[i])

        result = await multi_judge.score(
            prompt="Test prompt",
            response="Test response"
        )

        assert result.high_variance is True
        assert result.needs_human_review is True

    def test_calibration_summary(self):
        """MultiJudge should generate calibration summary."""
        from eval.judge.ensemble import MultiJudge, EnsembleResult

        multi_judge = MultiJudge(judge_models=["model1", "model2"])

        results = [
            EnsembleResult(
                weighted_score=0.7,
                passed=True,
                individual_scores=[
                    {"judge_model": "model1", "weighted_score": 0.7},
                    {"judge_model": "model2", "weighted_score": 0.7},
                ],
                agreement=0.9,
                high_variance=False,
                needs_human_review=False,
                aggregation_method="median",
            ),
            EnsembleResult(
                weighted_score=0.5,
                passed=False,
                individual_scores=[
                    {"judge_model": "model1", "weighted_score": 0.5},
                    {"judge_model": "model2", "weighted_score": 0.5},
                ],
                agreement=1.0,
                high_variance=False,
                needs_human_review=False,
                aggregation_method="median",
            ),
        ]

        summary = multi_judge.get_calibration_summary(results)

        assert summary["total_evaluations"] == 2
        assert summary["pass_rate"] == 0.5
        assert "judge_statistics" in summary


class TestPairwiseScorer:
    """Tests for pairwise comparison."""

    def test_parse_pairwise_response(self):
        """Should parse pairwise comparison response."""
        from eval.judge.pairwise import parse_pairwise_response

        response = '''Based on my analysis:

```json
{
  "winner": "A",
  "criteria_verdicts": {
    "depth": {"winner": "A", "explanation": "More thorough"}
  },
  "overall_explanation": "Response A is better",
  "confidence": 0.9
}
```
'''
        parsed = parse_pairwise_response(response)

        assert parsed is not None
        assert parsed["winner"] == "A"
        assert parsed["confidence"] == 0.9

    @pytest.mark.asyncio
    async def test_pairwise_compare_maps_winner_correctly(self):
        """PairwiseScorer should map winner back to original labels."""
        from eval.judge.pairwise import PairwiseScorer

        # Mock inspect_ai.model imports
        with patch.dict('sys.modules', {
            'inspect_ai': MagicMock(),
            'inspect_ai.model': MagicMock(
                ChatMessageSystem=MagicMock(),
                ChatMessageUser=MagicMock(),
            ),
        }):
            comparer = PairwiseScorer(randomize_order=False)

            # Mock model
            mock_model = AsyncMock()
            mock_response = MagicMock()
            mock_response.completion = '''{"winner": "A", "criteria_verdicts": {}, "overall_explanation": "A is better", "confidence": 0.9}'''
            mock_model.generate = AsyncMock(return_value=mock_response)
            comparer._model = mock_model

            result = await comparer.compare(
                prompt="Test prompt",
                response_1="First response",
                response_2="Second response",
                label_1="baseline",
                label_2="new_model",
            )

            # Winner A with no swap means response_1 (baseline) wins
            assert result["winner"] == "response_1"
            assert result["winner_label"] == "baseline"

    @pytest.mark.asyncio
    async def test_pairwise_handles_tie(self):
        """PairwiseScorer should handle ties correctly."""
        from eval.judge.pairwise import PairwiseScorer

        # Mock inspect_ai.model imports
        with patch.dict('sys.modules', {
            'inspect_ai': MagicMock(),
            'inspect_ai.model': MagicMock(
                ChatMessageSystem=MagicMock(),
                ChatMessageUser=MagicMock(),
            ),
        }):
            comparer = PairwiseScorer(randomize_order=False)

            mock_model = AsyncMock()
            mock_response = MagicMock()
            mock_response.completion = '''{"winner": "TIE", "criteria_verdicts": {}, "overall_explanation": "Equal", "confidence": 0.8}'''
            mock_model.generate = AsyncMock(return_value=mock_response)
            comparer._model = mock_model

            result = await comparer.compare(
                prompt="Test prompt",
                response_1="First",
                response_2="Second",
            )

            assert result["winner"] == "tie"
            assert result["winner_label"] is None


class TestCLIJudgeCommands:
    """Tests for CLI judge commands."""

    def test_judge_command_exists(self):
        """judge command should be registered."""
        from click.testing import CliRunner
        from eval.cli import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["judge", "--help"])

        assert result.exit_code == 0
        assert "Evaluate a response using LLM-as-Judge" in result.output

    def test_compare_responses_command_exists(self):
        """compare-responses command should be registered."""
        from click.testing import CliRunner
        from eval.cli import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["compare-responses", "--help"])

        assert result.exit_code == 0
        assert "Compare two responses head-to-head" in result.output

    def test_judge_file_command_exists(self):
        """judge-file command should be registered."""
        from click.testing import CliRunner
        from eval.cli import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["judge-file", "--help"])

        assert result.exit_code == 0
        assert "Evaluate multiple responses from a JSON file" in result.output

"""Multi-judge ensemble for robust LLM-as-Judge evaluation.

Uses multiple judge models to reduce bias and increase reliability.
Supports different aggregation strategies.
"""

import asyncio
from dataclasses import dataclass
from statistics import median, stdev
from typing import Optional

from .rubric import Rubric, DEFAULT_REASONING_RUBRIC
from .scorer import JudgeScorer


# Default diverse judge panel - top-tier models only for reliable evaluation
DEFAULT_JUDGE_MODELS = [
    "anthropic/claude-opus-4-5-20251101",  # Claude Opus 4.5
    "openai/gpt-5.2",                       # GPT-5.2
    "google/gemini-3-pro-preview",          # Gemini 3 Pro
]


@dataclass
class EnsembleResult:
    """Result from multi-judge evaluation.

    Attributes:
        weighted_score: Aggregated weighted score (0.0-1.0)
        passed: Whether response meets threshold
        individual_scores: List of per-judge results
        agreement: Inter-judge agreement metric (0.0-1.0)
        high_variance: True if judges significantly disagree
        needs_human_review: True if disagreement suggests human review
    """
    weighted_score: float
    passed: bool
    individual_scores: list[dict]
    agreement: float
    high_variance: bool
    needs_human_review: bool
    aggregation_method: str


class MultiJudge:
    """Multi-judge ensemble for robust evaluation.

    Queries multiple judge models in parallel and aggregates their scores
    using configurable strategies. Flags high-variance cases for human review.
    """

    def __init__(
        self,
        rubric: Optional[Rubric] = None,
        judge_models: Optional[list[str]] = None,
        pass_threshold: float = 0.6,
        variance_threshold: float = 0.15,
        aggregation: str = "median",
    ):
        """Initialize MultiJudge.

        Args:
            rubric: Evaluation rubric (defaults to reasoning rubric)
            judge_models: List of models to use as judges
            pass_threshold: Minimum weighted score to pass (0.0-1.0)
            variance_threshold: Score variance above which to flag for review
            aggregation: Aggregation method ("median", "mean", "majority")
        """
        self.rubric = rubric or DEFAULT_REASONING_RUBRIC
        self.judge_models = judge_models or DEFAULT_JUDGE_MODELS
        self.pass_threshold = pass_threshold
        self.variance_threshold = variance_threshold
        self.aggregation = aggregation

        # Create individual judge scorers
        self._judges = [
            JudgeScorer(
                rubric=self.rubric,
                judge_model=model,
                pass_threshold=pass_threshold,
            )
            for model in self.judge_models
        ]

    async def score(
        self,
        prompt: str,
        response: str,
    ) -> EnsembleResult:
        """Score a response using all judges in parallel.

        Args:
            prompt: The original prompt/question
            response: The AI response to evaluate

        Returns:
            EnsembleResult with aggregated scores and metadata
        """
        # Query all judges in parallel
        tasks = [
            judge.score(prompt, response)
            for judge in self._judges
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out failed judges
        valid_results = []
        for model, result in zip(self.judge_models, results):
            if isinstance(result, Exception):
                valid_results.append({
                    "judge_model": model,
                    "weighted_score": 0.0,
                    "passed": False,
                    "error": str(result),
                })
            elif result.get("parse_error"):
                valid_results.append({
                    "judge_model": model,
                    "weighted_score": 0.0,
                    "passed": False,
                    "error": "Failed to parse judge response",
                })
            else:
                result["judge_model"] = model
                valid_results.append(result)

        # Get scores from valid results (excluding errors)
        scores = [r["weighted_score"] for r in valid_results if "error" not in r]

        if not scores:
            # All judges failed
            return EnsembleResult(
                weighted_score=0.0,
                passed=False,
                individual_scores=valid_results,
                agreement=0.0,
                high_variance=True,
                needs_human_review=True,
                aggregation_method=self.aggregation,
            )

        # Aggregate scores
        if self.aggregation == "median":
            final_score = median(scores)
        elif self.aggregation == "mean":
            final_score = sum(scores) / len(scores)
        elif self.aggregation == "majority":
            # Majority vote on pass/fail
            passed_count = sum(1 for s in scores if s >= self.pass_threshold)
            final_score = 1.0 if passed_count > len(scores) / 2 else 0.0
        else:
            final_score = median(scores)

        # Calculate variance and agreement
        if len(scores) >= 2:
            score_stdev = stdev(scores)
            score_range = max(scores) - min(scores)
        else:
            score_stdev = 0.0
            score_range = 0.0

        # Agreement: 1 - normalized range
        agreement = 1.0 - min(score_range, 1.0)

        # High variance check
        high_variance = score_stdev > self.variance_threshold

        # Flag for human review if high variance or borderline score
        borderline = abs(final_score - self.pass_threshold) < 0.1
        needs_human_review = high_variance or (borderline and score_range > 0.2)

        return EnsembleResult(
            weighted_score=final_score,
            passed=final_score >= self.pass_threshold,
            individual_scores=valid_results,
            agreement=agreement,
            high_variance=high_variance,
            needs_human_review=needs_human_review,
            aggregation_method=self.aggregation,
        )

    async def score_batch(
        self,
        samples: list[tuple[str, str]],
        max_concurrent: int = 5,
    ) -> list[EnsembleResult]:
        """Score multiple samples with controlled concurrency.

        Args:
            samples: List of (prompt, response) tuples
            max_concurrent: Maximum concurrent evaluations

        Returns:
            List of EnsembleResult for each sample
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def score_with_limit(prompt: str, response: str) -> EnsembleResult:
            async with semaphore:
                return await self.score(prompt, response)

        tasks = [
            score_with_limit(prompt, response)
            for prompt, response in samples
        ]

        return await asyncio.gather(*tasks)

    def get_calibration_summary(self, results: list[EnsembleResult]) -> dict:
        """Generate calibration summary across multiple evaluations.

        Useful for tracking judge drift and identifying systematic biases.

        Args:
            results: List of evaluation results

        Returns:
            Dictionary with calibration metrics
        """
        if not results:
            return {"error": "No results to analyze"}

        all_scores = [r.weighted_score for r in results]
        agreements = [r.agreement for r in results]
        high_var_count = sum(1 for r in results if r.high_variance)
        review_count = sum(1 for r in results if r.needs_human_review)

        # Per-judge statistics
        judge_stats = {model: {"scores": [], "errors": 0} for model in self.judge_models}

        for result in results:
            for individual in result.individual_scores:
                model = individual.get("judge_model", "unknown")
                if model in judge_stats:
                    if "error" in individual:
                        judge_stats[model]["errors"] += 1
                    else:
                        judge_stats[model]["scores"].append(individual["weighted_score"])

        # Calculate per-judge averages
        for model, stats in judge_stats.items():
            if stats["scores"]:
                stats["mean_score"] = sum(stats["scores"]) / len(stats["scores"])
                stats["score_count"] = len(stats["scores"])
            else:
                stats["mean_score"] = None
                stats["score_count"] = 0

        return {
            "total_evaluations": len(results),
            "mean_score": sum(all_scores) / len(all_scores),
            "mean_agreement": sum(agreements) / len(agreements),
            "high_variance_rate": high_var_count / len(results),
            "human_review_rate": review_count / len(results),
            "pass_rate": sum(1 for r in results if r.passed) / len(results),
            "judge_statistics": judge_stats,
        }

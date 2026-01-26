"""LLM-as-Judge evaluation system for open-ended reasoning.

This module provides tools for evaluating AI responses using LLM judges
instead of requiring ground truth answers. Useful for evaluating:
- Open-ended reasoning quality
- Debate/deliberation outputs
- Creative problem-solving
- Multi-perspective analysis

Components:
- Rubric: Defines evaluation criteria with weights and anchors
- JudgeScorer: Single-judge evaluation using a rubric
- MultiJudge: Multi-judge ensemble for bias reduction
- PairwiseScorer: A/B comparison between responses

Inspect AI integration is lazy-loaded to avoid hard dependency.
"""

from .rubric import Rubric, Criterion, load_rubric, save_rubric
from .rubric import DEFAULT_REASONING_RUBRIC, DEFAULT_DEBATE_RUBRIC

# Core classes that don't need inspect_ai at import time
from .scorer import JudgeScorer, parse_judge_response, calculate_weighted_score
from .ensemble import MultiJudge, EnsembleResult
from .pairwise import PairwiseScorer, parse_pairwise_response


def judge_scorer(*args, **kwargs):
    """Create an inspect_ai scorer using LLM-as-Judge evaluation.

    Requires inspect_ai to be installed.
    """
    from .scorer import judge_scorer as _judge_scorer
    return _judge_scorer(*args, **kwargs)


def pairwise_scorer(*args, **kwargs):
    """Create an inspect_ai scorer for pairwise comparison.

    Requires inspect_ai to be installed.
    """
    from .pairwise import pairwise_scorer as _pairwise_scorer
    return _pairwise_scorer(*args, **kwargs)


__all__ = [
    # Rubric
    "Rubric",
    "Criterion",
    "load_rubric",
    "save_rubric",
    "DEFAULT_REASONING_RUBRIC",
    "DEFAULT_DEBATE_RUBRIC",
    # Single Judge
    "JudgeScorer",
    "judge_scorer",
    "parse_judge_response",
    "calculate_weighted_score",
    # Multi Judge
    "MultiJudge",
    "EnsembleResult",
    # Pairwise
    "PairwiseScorer",
    "pairwise_scorer",
    "parse_pairwise_response",
]

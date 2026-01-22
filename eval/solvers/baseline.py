"""Baseline solver - standard single-model evaluation."""

from typing import Any
from . import Solver


class BaselineSolver(Solver):
    """Standard single-model solver using Inspect's native generate().

    This is the simplest solver - it just calls the model once
    with the problem and returns the response. Used as a baseline
    for comparing more sophisticated approaches.
    """
    name = "baseline"

    def __init__(self, model: str = "anthropic/claude-sonnet-4-20250514"):
        """Initialize with target model.

        Args:
            model: Model identifier (e.g., "anthropic/claude-sonnet-4-20250514")
        """
        self.model = model

    async def solve(self, state: Any, generate: Any) -> Any:
        """Generate solution using standard model call.

        This delegates to Inspect's generate() which handles
        the actual API call and response parsing.
        """
        return await generate(state)

    @property
    def metadata(self) -> dict:
        """Return solver metadata for logging."""
        return {
            "name": self.name,
            "model": self.model,
        }

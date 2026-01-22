"""Base class for evaluation solvers."""

from abc import ABC, abstractmethod
from typing import Any


class Solver(ABC):
    """Base class for evaluation solvers.

    Solvers transform task state, potentially through multiple turns
    of model interaction and tool use.
    """
    name: str = "base"

    @abstractmethod
    async def solve(self, state: Any, generate: Any) -> Any:
        """Transform task state to produce a solution.

        Args:
            state: Inspect TaskState with input, messages, tools
            generate: Inspect generate function for model calls

        Returns:
            Updated TaskState with solution
        """
        pass

    async def setup(self, state: Any) -> None:
        """Optional: Initialize solver state before run."""
        pass

    async def teardown(self) -> None:
        """Optional: Cleanup after run."""
        pass

    @property
    def metadata(self) -> dict:
        """Solver-specific metadata for logging."""
        return {"name": self.name}

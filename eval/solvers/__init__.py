"""Pluggable solver system for evaluation.

Solvers define how models approach benchmark problems.
- baseline: Standard single-model approach
- minds: Multi-model collaboration
- custom: User-defined solvers
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, Type


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


# Global solver registry
_SOLVER_REGISTRY: dict[str, Type[Solver]] = {}


def register_solver(name: str, solver_class: Type[Solver]):
    """Register a solver class by name."""
    _SOLVER_REGISTRY[name] = solver_class


def get_solver(name: str) -> Type[Solver]:
    """Get a solver class by name.

    Raises:
        KeyError: If solver not found
    """
    if name not in _SOLVER_REGISTRY:
        raise KeyError(f"Unknown solver: {name}. Available: {list(_SOLVER_REGISTRY.keys())}")
    return _SOLVER_REGISTRY[name]


def list_solvers() -> list[str]:
    """List all registered solver names."""
    return list(_SOLVER_REGISTRY.keys())


# Import and register built-in solvers
from .baseline import BaselineSolver
register_solver("baseline", BaselineSolver)

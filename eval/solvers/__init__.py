"""Pluggable solver system for evaluation.

Solvers define how models approach benchmark problems.
- baseline: Standard single-model approach
- minds: Multi-model collaboration
- custom: User-defined solvers
"""

from typing import Any, Optional, Type
from .base import Solver


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

from .minds import MindsSolver
register_solver("minds", MindsSolver)

"""Tests for eval/solvers - Solver base class and registry."""

import pytest


class TestSolverRegistry:
    """Tests for solver registration and lookup."""

    def test_register_solver(self):
        """Should register a solver class."""
        from eval.solvers import register_solver, get_solver, Solver

        class CustomSolver(Solver):
            name = "custom"

            async def solve(self, state, generate):
                return state

        register_solver("custom", CustomSolver)

        retrieved = get_solver("custom")
        assert retrieved == CustomSolver

    def test_get_unknown_solver(self):
        """Should raise KeyError for unknown solver."""
        from eval.solvers import get_solver

        with pytest.raises(KeyError):
            get_solver("nonexistent")

    def test_baseline_solver_registered(self):
        """Baseline solver should be pre-registered."""
        from eval.solvers import get_solver

        solver_class = get_solver("baseline")
        assert solver_class is not None
        assert solver_class.name == "baseline"

    def test_list_solvers(self):
        """Should list all registered solvers."""
        from eval.solvers import list_solvers

        solvers = list_solvers()
        assert "baseline" in solvers


class TestBaselineSolver:
    """Tests for BaselineSolver."""

    def test_baseline_solver_metadata(self):
        """Baseline solver should have correct metadata."""
        from eval.solvers.baseline import BaselineSolver

        solver = BaselineSolver(model="anthropic/claude-sonnet-4-20250514")

        assert solver.name == "baseline"
        assert solver.model == "anthropic/claude-sonnet-4-20250514"
        assert solver.metadata["model"] == "anthropic/claude-sonnet-4-20250514"

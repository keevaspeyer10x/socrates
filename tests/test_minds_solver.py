"""Tests for eval/solvers/minds.py - Multi-model collaboration solver."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestMindsSolver:
    """Tests for MindsSolver class."""

    def test_initialization_default_models(self):
        """MindsSolver should initialize with default model list."""
        from eval.solvers.minds import MindsSolver, DEFAULT_MODELS

        solver = MindsSolver()
        assert solver.models == DEFAULT_MODELS
        assert len(solver.models) == 5  # 5 top models from multiminds

    def test_initialization_custom_models(self):
        """MindsSolver should accept custom model list."""
        from eval.solvers.minds import MindsSolver

        custom_models = ["anthropic/claude-opus-4-5-20251101", "openai/gpt-5.2"]
        solver = MindsSolver(models=custom_models)
        assert solver.models == custom_models

    def test_initialization_synthesizer(self):
        """MindsSolver should have configurable synthesizer model."""
        from eval.solvers.minds import MindsSolver

        solver = MindsSolver(synthesizer_model="anthropic/claude-sonnet-4-20250514")
        assert solver.synthesizer_model == "anthropic/claude-sonnet-4-20250514"

    def test_metadata(self):
        """Metadata should include name, models, and synthesizer."""
        from eval.solvers.minds import MindsSolver

        solver = MindsSolver()
        metadata = solver.metadata

        assert metadata["name"] == "minds"
        assert "models" in metadata
        assert "synthesizer" in metadata
        assert len(metadata["models"]) == 5

    def test_solver_name(self):
        """Solver name should be 'minds'."""
        from eval.solvers.minds import MindsSolver

        solver = MindsSolver()
        assert solver.name == "minds"


class TestMindsSolverRegistration:
    """Tests for MindsSolver registration in solver registry."""

    def test_minds_solver_registered(self):
        """MindsSolver should be registered in the solver registry."""
        from eval.solvers import list_solvers, get_solver

        assert "minds" in list_solvers()

    def test_get_minds_solver(self):
        """Should be able to retrieve MindsSolver by name."""
        from eval.solvers import get_solver
        from eval.solvers.minds import MindsSolver

        solver_class = get_solver("minds")
        assert solver_class == MindsSolver


class TestMindsSolverSolve:
    """Tests for MindsSolver.solve() method."""

    @pytest.mark.asyncio
    async def test_solve_calls_all_models(self):
        """solve() should query all configured models."""
        from eval.solvers.minds import MindsSolver

        solver = MindsSolver(models=["model_a", "model_b", "model_c"])

        # Mock the internal _query_model method
        with patch.object(solver, '_query_model', new_callable=AsyncMock) as mock_query:
            mock_query.return_value = "response"

            # Mock the _synthesize method
            with patch.object(solver, '_synthesize', new_callable=AsyncMock) as mock_synth:
                mock_synth.return_value = MagicMock()

                mock_state = MagicMock()
                mock_generate = AsyncMock()

                await solver.solve(mock_state, mock_generate)

                # Should have called _query_model for each model
                assert mock_query.call_count == 3

    @pytest.mark.asyncio
    async def test_solve_synthesizes_responses(self):
        """solve() should synthesize responses from all models."""
        from eval.solvers.minds import MindsSolver

        solver = MindsSolver(models=["model_a", "model_b"])

        with patch.object(solver, '_query_model', new_callable=AsyncMock) as mock_query:
            mock_query.side_effect = ["Response A", "Response B"]

            with patch.object(solver, '_synthesize', new_callable=AsyncMock) as mock_synth:
                mock_synth.return_value = MagicMock()

                mock_state = MagicMock()
                mock_generate = AsyncMock()

                await solver.solve(mock_state, mock_generate)

                # _synthesize should have been called with all responses
                mock_synth.assert_called_once()
                call_args = mock_synth.call_args
                responses = call_args[0][1]  # Second positional arg
                assert len(responses) == 2

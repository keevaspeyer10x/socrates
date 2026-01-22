"""Tests for eval/learning.py - Learning pipeline and lesson management."""

import json
import pytest
from pathlib import Path


class TestCandidateLesson:
    """Tests for CandidateLesson data model."""

    def test_create_candidate_lesson(self):
        """Should create CandidateLesson with required fields."""
        from eval.learning import CandidateLesson

        candidate = CandidateLesson(
            lesson_id="test_lesson_001",
            episode_ids=["ep_001", "ep_002"],
            what="Check input bounds before arithmetic",
            why="Multiple episodes failed due to division by zero",
            expected="Reduce arithmetic errors",
            triggers=["arithmetic", "division"],
            confidence=0.85,
        )

        assert candidate.lesson_id == "test_lesson_001"
        assert len(candidate.episode_ids) == 2
        assert candidate.confidence == 0.85
        assert candidate.status == "draft"

    def test_candidate_to_json(self):
        """CandidateLesson should serialize to JSON."""
        from eval.learning import CandidateLesson

        candidate = CandidateLesson(
            lesson_id="test_001",
            episode_ids=["ep_001"],
            what="Test what",
            why="Test why",
            expected="Test expected",
            triggers=["test"],
            confidence=0.5,
        )

        json_str = candidate.to_json()
        parsed = json.loads(json_str)

        assert parsed["lesson_id"] == "test_001"
        assert parsed["confidence"] == 0.5

    def test_promote_to_lesson_card(self):
        """CandidateLesson.promote() should create LessonCard."""
        from eval.learning import CandidateLesson, LessonCard

        candidate = CandidateLesson(
            lesson_id="test_001",
            episode_ids=["ep_001", "ep_002"],
            what="Check bounds",
            why="Prevents errors",
            expected="Fewer failures",
            triggers=["arithmetic"],
            confidence=0.9,
            source_benchmark="gsm8k",
            source_solver="baseline",
        )

        lesson = candidate.promote()

        assert isinstance(lesson, LessonCard)
        assert lesson.lesson_id == candidate.lesson_id
        assert lesson.what == candidate.what
        assert lesson.status == "approved"
        assert lesson.evidence_refs == candidate.episode_ids


class TestLessonCard:
    """Tests for LessonCard data model."""

    def test_create_lesson_card(self):
        """Should create LessonCard with required fields."""
        from eval.learning import LessonCard

        lesson = LessonCard(
            lesson_id="lesson_001",
            what="Verify answer format",
            why="Reduces format mismatches",
            expected="Higher pass rate",
            triggers=["output", "formatting"],
            evidence_refs=["ep_001"],
            confidence=0.8,
        )

        assert lesson.lesson_id == "lesson_001"
        assert lesson.status == "approved"
        assert lesson.version == 1
        assert lesson.application_count == 0

    def test_dedupe_hash_computed(self):
        """LessonCard should compute dedupe hash automatically."""
        from eval.learning import LessonCard

        lesson = LessonCard(
            lesson_id="lesson_001",
            what="Verify answer format",
            why="Reduces errors",
            expected="Better results",
            triggers=["output"],
            evidence_refs=[],
            confidence=0.8,
        )

        assert lesson.dedupe_hash is not None
        assert len(lesson.dedupe_hash) == 16  # SHA256 truncated to 16 chars

    def test_record_application(self):
        """record_application should update stats."""
        from eval.learning import LessonCard

        lesson = LessonCard(
            lesson_id="lesson_001",
            what="Test",
            why="Test",
            expected="Test",
            triggers=[],
            evidence_refs=[],
            confidence=0.8,
        )

        # First application
        lesson.record_application(success=True)
        assert lesson.application_count == 1
        assert lesson.success_rate == 1.0
        assert lesson.last_applied is not None

        # Second application (failure)
        lesson.record_application(success=False)
        assert lesson.application_count == 2
        assert lesson.success_rate == 0.5

    def test_format_for_injection(self):
        """format_for_injection should create prompt-ready string."""
        from eval.learning import LessonCard

        lesson = LessonCard(
            lesson_id="lesson_001",
            what="Check bounds before arithmetic",
            why="Prevents division by zero",
            expected="Fewer crashes",
            triggers=["math"],
            evidence_refs=[],
            confidence=0.9,
        )

        formatted = lesson.format_for_injection()
        assert "Check bounds before arithmetic" in formatted
        assert "Prevents division by zero" in formatted


class TestLearningEngine:
    """Tests for LearningEngine class."""

    def test_create_engine(self, tmp_path):
        """Should create LearningEngine with directory structure."""
        from eval.learning import LearningEngine

        engine = LearningEngine(lessons_dir=tmp_path / "lessons")

        assert (tmp_path / "lessons").exists()
        assert (tmp_path / "lessons" / "candidates").exists()
        assert (tmp_path / "lessons" / "approved").exists()

    def test_save_and_load_candidate(self, tmp_path):
        """Should save and load candidate lessons."""
        from eval.learning import LearningEngine, CandidateLesson

        engine = LearningEngine(lessons_dir=tmp_path / "lessons")

        candidate = CandidateLesson(
            lesson_id="candidate_001",
            episode_ids=["ep_001"],
            what="Test lesson",
            why="For testing",
            expected="Test passes",
            triggers=["test"],
            confidence=0.7,
        )

        engine.save_candidate(candidate)

        # Load and verify
        candidates = engine.load_candidates()
        assert len(candidates) == 1
        assert candidates[0].lesson_id == "candidate_001"

    def test_save_and_load_lesson(self, tmp_path):
        """Should save and load approved lessons."""
        from eval.learning import LearningEngine, LessonCard

        engine = LearningEngine(lessons_dir=tmp_path / "lessons")

        lesson = LessonCard(
            lesson_id="lesson_001",
            what="Test lesson",
            why="For testing",
            expected="Test passes",
            triggers=["test"],
            evidence_refs=["ep_001"],
            confidence=0.8,
        )

        engine.save_lesson(lesson)

        # Load and verify
        lessons = engine.load_lessons()
        assert len(lessons) == 1
        assert lessons[0].lesson_id == "lesson_001"

    def test_approve_candidate(self, tmp_path):
        """Should approve candidate and promote to lesson."""
        from eval.learning import LearningEngine, CandidateLesson

        engine = LearningEngine(lessons_dir=tmp_path / "lessons")

        candidate = CandidateLesson(
            lesson_id="candidate_001",
            episode_ids=["ep_001"],
            what="Test lesson",
            why="For testing",
            expected="Test passes",
            triggers=["test"],
            confidence=0.7,
        )
        engine.save_candidate(candidate)

        # Approve
        lesson = engine.approve_candidate("candidate_001")

        assert lesson is not None
        assert lesson.status == "approved"

        # Candidate should be removed
        candidates = engine.load_candidates()
        assert len(candidates) == 0

        # Lesson should exist
        lessons = engine.load_lessons()
        assert len(lessons) == 1

    def test_reject_candidate(self, tmp_path):
        """Should reject and delete candidate."""
        from eval.learning import LearningEngine, CandidateLesson

        engine = LearningEngine(lessons_dir=tmp_path / "lessons")

        candidate = CandidateLesson(
            lesson_id="candidate_001",
            episode_ids=["ep_001"],
            what="Test lesson",
            why="For testing",
            expected="Test passes",
            triggers=["test"],
            confidence=0.7,
        )
        engine.save_candidate(candidate)

        # Reject
        result = engine.reject_candidate("candidate_001")

        assert result is True

        # Should be gone
        candidates = engine.load_candidates()
        assert len(candidates) == 0

    def test_extract_lessons_from_episodes(self, tmp_path):
        """Should extract lessons from episode data."""
        from eval.learning import LearningEngine

        engine = LearningEngine(lessons_dir=tmp_path / "lessons")

        # Create sample episodes with failures
        episodes = [
            {
                "sample_id": "ep_001",
                "outcome": {"passed": False, "failure_mode": "wrong_answer"}
            },
            {
                "sample_id": "ep_002",
                "outcome": {"passed": False, "failure_mode": "wrong_answer"}
            },
            {
                "sample_id": "ep_003",
                "outcome": {"passed": False, "failure_mode": "wrong_answer"}
            },
            {
                "sample_id": "ep_004",
                "outcome": {"passed": True}
            },
        ]

        candidates = engine.extract_lessons_from_episodes(
            episodes,
            run_id="test_run",
            benchmark="gsm8k",
            solver="baseline"
        )

        # Should extract at least one lesson for the dominant failure mode
        assert len(candidates) >= 1
        assert any("wrong_answer" in c.lesson_id for c in candidates)

    def test_retrieve_relevant_lessons(self, tmp_path):
        """Should retrieve lessons based on context."""
        from eval.learning import LearningEngine, LessonCard

        engine = LearningEngine(lessons_dir=tmp_path / "lessons")

        # Add some lessons
        lesson1 = LessonCard(
            lesson_id="lesson_math",
            what="Check arithmetic bounds",
            why="Prevents errors",
            expected="Better results",
            triggers=["arithmetic", "math", "calculation"],
            evidence_refs=[],
            confidence=0.9,
            source_benchmark="gsm8k",
        )
        lesson2 = LessonCard(
            lesson_id="lesson_format",
            what="Verify output format",
            why="Reduces mismatches",
            expected="Higher pass rate",
            triggers=["output", "formatting", "answer"],
            evidence_refs=[],
            confidence=0.8,
        )
        engine.save_lesson(lesson1)
        engine.save_lesson(lesson2)

        # Retrieve for math context
        relevant = engine.retrieve_relevant_lessons(
            "Solve this arithmetic problem: 5 + 3",
            benchmark="gsm8k"
        )

        assert len(relevant) > 0
        # Math lesson should be ranked higher for arithmetic context
        assert relevant[0].lesson_id == "lesson_math"

    def test_format_lessons_for_prompt(self, tmp_path):
        """Should format lessons for prompt injection."""
        from eval.learning import LearningEngine, LessonCard

        engine = LearningEngine(lessons_dir=tmp_path / "lessons")

        lessons = [
            LessonCard(
                lesson_id="lesson_001",
                what="Check bounds",
                why="Prevents errors",
                expected="Better",
                triggers=[],
                evidence_refs=[],
                confidence=0.9,
            ),
            LessonCard(
                lesson_id="lesson_002",
                what="Verify format",
                why="Reduces issues",
                expected="Higher rate",
                triggers=[],
                evidence_refs=[],
                confidence=0.8,
            ),
        ]

        formatted = engine.format_lessons_for_prompt(lessons)

        assert "<lessons>" in formatted
        assert "</lessons>" in formatted
        assert "Check bounds" in formatted
        assert "Verify format" in formatted

    def test_get_statistics(self, tmp_path):
        """Should return accurate statistics."""
        from eval.learning import LearningEngine, LessonCard, CandidateLesson

        engine = LearningEngine(lessons_dir=tmp_path / "lessons")

        # Add lessons and candidates
        engine.save_lesson(LessonCard(
            lesson_id="lesson_001",
            what="Test",
            why="Test",
            expected="Test",
            triggers=[],
            evidence_refs=[],
            confidence=0.8,
        ))
        engine.save_candidate(CandidateLesson(
            lesson_id="candidate_001",
            episode_ids=[],
            what="Test",
            why="Test",
            expected="Test",
            triggers=[],
            confidence=0.6,
        ))

        stats = engine.get_statistics()

        assert stats["total_lessons"] == 1
        assert stats["total_candidates"] == 1
        assert stats["approved_lessons"] == 1
        assert stats["avg_confidence"] == 0.8


class TestBaselineSolverLessonInjection:
    """Tests for lesson injection in BaselineSolver."""

    def test_baseline_with_lesson_injection_disabled(self):
        """BaselineSolver should work without lesson injection."""
        from eval.solvers.baseline import BaselineSolver

        solver = BaselineSolver(inject_lessons=False)
        assert solver.inject_lessons is False
        assert solver._learning_engine is None

    def test_baseline_with_lesson_injection_enabled(self, tmp_path):
        """BaselineSolver should enable lesson injection."""
        from eval.solvers.baseline import BaselineSolver

        solver = BaselineSolver(
            inject_lessons=True,
            lessons_dir=tmp_path / "lessons"
        )
        assert solver.inject_lessons is True

    def test_metadata_includes_injection_info(self):
        """Metadata should include injection settings."""
        from eval.solvers.baseline import BaselineSolver

        solver = BaselineSolver(inject_lessons=True, max_lessons=5)
        metadata = solver.metadata

        assert metadata["inject_lessons"] is True
        assert metadata["max_lessons"] == 5

    def test_extract_context(self):
        """Should extract context from state."""
        from eval.solvers.baseline import BaselineSolver
        from unittest.mock import MagicMock

        solver = BaselineSolver()

        # Mock state with input
        state = MagicMock()
        state.input = "What is 2+2?"
        state.messages = []

        context = solver._extract_context(state)
        assert "2+2" in context


class TestCustomSolverLoading:
    """Tests for custom solver loading (Phase 5)."""

    def test_load_solver_from_file(self, tmp_path):
        """Should load custom solver from Python file."""
        from eval.solvers import load_custom_solver, Solver

        # Create a custom solver file
        solver_code = '''
from eval.solvers.base import Solver
from typing import Any

class MyCustomSolver(Solver):
    name = "my_custom"

    async def solve(self, state: Any, generate: Any) -> Any:
        return state
'''
        solver_file = tmp_path / "my_solver.py"
        solver_file.write_text(solver_code)

        # Load it
        solver_class = load_custom_solver(str(solver_file))

        assert solver_class.name == "my_custom"
        assert issubclass(solver_class, Solver)

    def test_load_solver_file_not_found(self):
        """Should raise FileNotFoundError for missing file."""
        from eval.solvers import load_custom_solver

        with pytest.raises(FileNotFoundError):
            load_custom_solver("/nonexistent/path/solver.py")

    def test_load_solver_no_solver_class(self, tmp_path):
        """Should raise ValueError if no Solver subclass found."""
        from eval.solvers import load_custom_solver

        # Create a file without Solver subclass
        bad_code = '''
class NotASolver:
    pass
'''
        bad_file = tmp_path / "bad_solver.py"
        bad_file.write_text(bad_code)

        with pytest.raises(ValueError, match="No Solver subclass"):
            load_custom_solver(str(bad_file))

    def test_create_solver_instance(self, tmp_path):
        """Should create solver instance from custom path."""
        from eval.solvers import create_solver_instance, Solver

        # Create a custom solver file
        solver_code = '''
from eval.solvers.base import Solver
from typing import Any

class ConfigurableSolver(Solver):
    name = "configurable"

    def __init__(self, value: str = "default"):
        self.value = value

    async def solve(self, state: Any, generate: Any) -> Any:
        return state
'''
        solver_file = tmp_path / "config_solver.py"
        solver_file.write_text(solver_code)

        # Create instance with kwargs
        instance = create_solver_instance(
            "configurable",
            custom_path=str(solver_file),
            value="custom_value"
        )

        assert instance.name == "configurable"
        assert instance.value == "custom_value"

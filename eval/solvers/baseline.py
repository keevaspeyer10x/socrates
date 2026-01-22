"""Baseline solver - standard single-model evaluation with lesson injection."""

from pathlib import Path
from typing import Any, Optional
from .base import Solver


class BaselineSolver(Solver):
    """Standard single-model solver using Inspect's native generate().

    This is the simplest solver - it just calls the model once
    with the problem and returns the response. Used as a baseline
    for comparing more sophisticated approaches.

    Supports optional lesson injection to test learning effectiveness.
    """
    name = "baseline"

    def __init__(
        self,
        model: str = "anthropic/claude-sonnet-4-20250514",
        inject_lessons: bool = False,
        lessons_dir: Optional[Path] = None,
        max_lessons: int = 3
    ):
        """Initialize with target model.

        Args:
            model: Model identifier (e.g., "anthropic/claude-sonnet-4-20250514")
            inject_lessons: Whether to inject relevant lessons into prompts
            lessons_dir: Directory containing lessons (default: eval_logs/lessons)
            max_lessons: Maximum lessons to inject per problem
        """
        self.model = model
        self.inject_lessons = inject_lessons
        self.lessons_dir = lessons_dir or Path("eval_logs/lessons")
        self.max_lessons = max_lessons
        self._learning_engine = None
        self._injected_lesson_ids: list[str] = []  # Track which lessons were used

    def _get_learning_engine(self):
        """Lazy load the learning engine."""
        if self._learning_engine is None and self.inject_lessons:
            from ..learning import LearningEngine
            self._learning_engine = LearningEngine(lessons_dir=self.lessons_dir)
        return self._learning_engine

    def _extract_context(self, state: Any) -> str:
        """Extract context string from state for lesson matching."""
        context_parts = []

        # Try to get input from various possible locations
        if hasattr(state, 'input'):
            context_parts.append(str(state.input)[:500])
        if hasattr(state, 'messages') and state.messages:
            for msg in state.messages[:2]:  # First couple messages
                if hasattr(msg, 'content'):
                    context_parts.append(str(msg.content)[:300])

        return " ".join(context_parts)

    def _inject_lessons_into_state(self, state: Any, benchmark: Optional[str] = None) -> Any:
        """Inject relevant lessons into the state's messages.

        Args:
            state: Inspect TaskState
            benchmark: Optional benchmark name for better matching

        Returns:
            Modified state with lessons injected
        """
        engine = self._get_learning_engine()
        if not engine:
            return state

        # Extract context for matching
        context = self._extract_context(state)

        # Retrieve relevant lessons
        lessons = engine.retrieve_relevant_lessons(
            context,
            benchmark=benchmark,
            max_lessons=self.max_lessons
        )

        if not lessons:
            return state

        # Format lessons for injection
        lessons_text = engine.format_lessons_for_prompt(lessons)

        # Track which lessons were injected
        self._injected_lesson_ids = [l.lesson_id for l in lessons]

        # Inject as a system message or prepend to first user message
        if hasattr(state, 'messages') and state.messages:
            from copy import deepcopy
            modified_state = deepcopy(state)

            # Find first user message and prepend lessons
            for i, msg in enumerate(modified_state.messages):
                if hasattr(msg, 'role') and msg.role == 'user':
                    # Prepend lessons to content
                    if hasattr(msg, 'content'):
                        lesson_prefix = f"""Before answering, consider these lessons from past evaluations:

{lessons_text}

Now, here is your task:

"""
                        msg.content = lesson_prefix + str(msg.content)
                    break

            return modified_state

        return state

    async def solve(self, state: Any, generate: Any) -> Any:
        """Generate solution using standard model call.

        This delegates to Inspect's generate() which handles
        the actual API call and response parsing.

        If inject_lessons is enabled, retrieves and injects relevant
        lessons before generating.
        """
        if self.inject_lessons:
            state = self._inject_lessons_into_state(state)

        return await generate(state)

    def record_outcome(self, passed: bool):
        """Record the outcome for injected lessons.

        Call this after evaluation to update lesson effectiveness.

        Args:
            passed: Whether the evaluation passed
        """
        if not self._injected_lesson_ids:
            return

        engine = self._get_learning_engine()
        if not engine:
            return

        # Update each injected lesson
        for lesson_id in self._injected_lesson_ids:
            if lesson_id in engine._lessons_cache:
                lesson = engine._lessons_cache[lesson_id]
                lesson.record_application(success=passed)
                engine.save_lesson(lesson)

        # Clear for next problem
        self._injected_lesson_ids = []

    @property
    def metadata(self) -> dict:
        """Return solver metadata for logging."""
        return {
            "name": self.name,
            "model": self.model,
            "inject_lessons": self.inject_lessons,
            "max_lessons": self.max_lessons if self.inject_lessons else 0,
            "injected_lessons": len(self._injected_lesson_ids),
        }

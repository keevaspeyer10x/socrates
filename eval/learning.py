"""Learning module for extracting lessons from evaluation episodes.

Implements the LEARN cycle from research:
L - Log: Capture all decisions, outcomes, failures
E - Exchange: Share lessons across agents
A - Articulate: Convert tacit patterns to explicit rules
R - Review: Periodic retrospectives on what worked
N - Next: Apply lessons to upcoming work

Key schemas:
- CandidateLesson: LLM-extracted, not yet approved
- LessonCard: Approved, retrievable knowledge
"""

import hashlib
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Literal, Any


LessonStatus = Literal["draft", "candidate", "approved", "embedded", "archived"]


@dataclass
class CandidateLesson:
    """LLM-extracted lesson, not yet approved.

    Represents a potential lesson extracted from episode analysis,
    requiring human review before promotion to LessonCard.
    """
    lesson_id: str
    episode_ids: list[str]  # Evidence links
    what: str               # What to do
    why: str                # Signal/error it addresses
    expected: str           # Expected improvement
    triggers: list[str]     # When to apply (failure patterns, contexts)
    confidence: float       # 0.0-1.0 confidence score
    status: Literal["draft", "candidate"] = "draft"
    created_at: Optional[str] = None
    source_benchmark: Optional[str] = None
    source_solver: Optional[str] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, data: dict) -> "CandidateLesson":
        """Create from dictionary."""
        return cls(**data)

    def promote(self) -> "LessonCard":
        """Promote to approved LessonCard.

        Returns a new LessonCard with approved status.
        """
        return LessonCard(
            lesson_id=self.lesson_id,
            what=self.what,
            why=self.why,
            expected=self.expected,
            triggers=self.triggers,
            evidence_refs=self.episode_ids,
            confidence=self.confidence,
            status="approved",
            source_benchmark=self.source_benchmark,
            source_solver=self.source_solver,
        )


@dataclass
class LessonCard:
    """Approved, retrievable knowledge.

    Represents validated learning that can be:
    - Retrieved for injection into future runs
    - Tracked for effectiveness
    - Embedded into workflow instructions
    """
    lesson_id: str
    what: str               # What to do
    why: str                # Signal/error it addresses
    expected: str           # Expected improvement
    triggers: list[str]     # When to apply
    evidence_refs: list[str]  # Episode IDs that support this lesson
    confidence: float       # 0.0-1.0 confidence score
    status: Literal["approved", "embedded", "archived"] = "approved"
    dedupe_hash: Optional[str] = None  # For exact dedup
    version: int = 1
    application_count: int = 0
    success_rate: float = 0.0  # When applied, how often it helped
    created_at: Optional[str] = None
    last_applied: Optional[str] = None
    source_benchmark: Optional[str] = None
    source_solver: Optional[str] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc).isoformat()
        if self.dedupe_hash is None:
            self.dedupe_hash = self._compute_hash()

    def _compute_hash(self) -> str:
        """Compute deduplication hash from content."""
        content = f"{self.what}|{self.why}|{'|'.join(sorted(self.triggers))}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, data: dict) -> "LessonCard":
        """Create from dictionary."""
        return cls(**data)

    def record_application(self, success: bool):
        """Record that this lesson was applied.

        Args:
            success: Whether the application was successful
        """
        old_count = self.application_count
        self.application_count += 1

        # Update success rate (rolling average)
        if old_count == 0:
            self.success_rate = 1.0 if success else 0.0
        else:
            self.success_rate = (
                (self.success_rate * old_count + (1.0 if success else 0.0))
                / self.application_count
            )

        self.last_applied = datetime.now(timezone.utc).isoformat()

    def format_for_injection(self) -> str:
        """Format lesson for prompt injection.

        Returns a concise string suitable for including in prompts.
        """
        return f"- {self.what} (Because: {self.why})"


# Extraction prompt for LLM-based lesson extraction
EXTRACTION_PROMPT = """Analyze these evaluation episodes and extract actionable lessons.

## Episodes:
{episodes_json}

## Task:
Extract 1-3 lessons from patterns you observe. Focus on:
1. Recurring failure patterns and how to avoid them
2. Successful strategies that could be generalized
3. Tool usage patterns that worked well or poorly

For each lesson, provide:
- what: A specific, actionable instruction (imperative form)
- why: The signal/error/pattern that makes this lesson valuable
- expected: What improvement we expect if this lesson is followed
- triggers: Contexts where this lesson applies (failure modes, problem types, etc.)
- confidence: How confident you are (0.0-1.0) based on evidence strength

## Output Format (JSON):
{{
  "lessons": [
    {{
      "what": "Check input bounds before arithmetic operations",
      "why": "Multiple episodes failed due to division by zero or overflow",
      "expected": "Reduce arithmetic errors by catching edge cases early",
      "triggers": ["arithmetic", "division", "numeric computation"],
      "confidence": 0.85
    }}
  ]
}}

Only output valid JSON, no additional text."""


class LearningEngine:
    """Engine for extracting and managing lessons from episodes.

    Responsibilities:
    - Extract candidate lessons from episode batches
    - Deduplicate similar lessons
    - Retrieve relevant lessons for new tasks
    - Track lesson effectiveness
    """

    def __init__(
        self,
        lessons_dir: Optional[Path] = None,
        model: str = "anthropic/claude-sonnet-4-20250514"
    ):
        """Initialize LearningEngine.

        Args:
            lessons_dir: Directory for storing lessons
            model: Model to use for extraction
        """
        self.lessons_dir = lessons_dir or Path("eval_logs/lessons")
        self.model = model
        self._lessons_cache: dict[str, LessonCard] = {}
        self._candidates_cache: dict[str, CandidateLesson] = {}

        # Ensure directories exist
        self.lessons_dir.mkdir(parents=True, exist_ok=True)
        (self.lessons_dir / "candidates").mkdir(exist_ok=True)
        (self.lessons_dir / "approved").mkdir(exist_ok=True)

    def load_lessons(self) -> list[LessonCard]:
        """Load all approved lessons from disk.

        Returns:
            List of approved LessonCards
        """
        lessons = []
        approved_dir = self.lessons_dir / "approved"

        if approved_dir.exists():
            for lesson_file in approved_dir.glob("*.json"):
                try:
                    data = json.loads(lesson_file.read_text())
                    lesson = LessonCard.from_dict(data)
                    lessons.append(lesson)
                    self._lessons_cache[lesson.lesson_id] = lesson
                except (json.JSONDecodeError, KeyError) as e:
                    # Skip malformed lesson files
                    continue

        return lessons

    def load_candidates(self) -> list[CandidateLesson]:
        """Load all candidate lessons from disk.

        Returns:
            List of CandidateLessons pending review
        """
        candidates = []
        candidates_dir = self.lessons_dir / "candidates"

        if candidates_dir.exists():
            for candidate_file in candidates_dir.glob("*.json"):
                try:
                    data = json.loads(candidate_file.read_text())
                    candidate = CandidateLesson.from_dict(data)
                    candidates.append(candidate)
                    self._candidates_cache[candidate.lesson_id] = candidate
                except (json.JSONDecodeError, KeyError):
                    continue

        return candidates

    def save_candidate(self, candidate: CandidateLesson):
        """Save a candidate lesson to disk.

        Args:
            candidate: CandidateLesson to save
        """
        path = self.lessons_dir / "candidates" / f"{candidate.lesson_id}.json"
        path.write_text(candidate.to_json())
        self._candidates_cache[candidate.lesson_id] = candidate

    def save_lesson(self, lesson: LessonCard):
        """Save an approved lesson to disk.

        Args:
            lesson: LessonCard to save
        """
        path = self.lessons_dir / "approved" / f"{lesson.lesson_id}.json"
        path.write_text(lesson.to_json())
        self._lessons_cache[lesson.lesson_id] = lesson

    def approve_candidate(self, candidate_id: str) -> Optional[LessonCard]:
        """Approve a candidate lesson and promote to LessonCard.

        Args:
            candidate_id: ID of candidate to approve

        Returns:
            New LessonCard if found, None otherwise
        """
        # Find candidate
        candidate_path = self.lessons_dir / "candidates" / f"{candidate_id}.json"
        if not candidate_path.exists():
            return None

        data = json.loads(candidate_path.read_text())
        candidate = CandidateLesson.from_dict(data)

        # Promote to lesson
        lesson = candidate.promote()

        # Save lesson
        self.save_lesson(lesson)

        # Remove candidate file
        candidate_path.unlink()
        if candidate_id in self._candidates_cache:
            del self._candidates_cache[candidate_id]

        return lesson

    def reject_candidate(self, candidate_id: str) -> bool:
        """Reject and delete a candidate lesson.

        Args:
            candidate_id: ID of candidate to reject

        Returns:
            True if found and deleted, False otherwise
        """
        candidate_path = self.lessons_dir / "candidates" / f"{candidate_id}.json"
        if not candidate_path.exists():
            return False

        candidate_path.unlink()
        if candidate_id in self._candidates_cache:
            del self._candidates_cache[candidate_id]

        return True

    def _is_duplicate(self, lesson: CandidateLesson) -> bool:
        """Check if a lesson is a duplicate of existing lessons.

        Args:
            lesson: Candidate to check

        Returns:
            True if duplicate found
        """
        # Compute hash for the candidate
        content = f"{lesson.what}|{lesson.why}|{'|'.join(sorted(lesson.triggers))}"
        candidate_hash = hashlib.sha256(content.encode()).hexdigest()[:16]

        # Check against approved lessons
        for existing in self._lessons_cache.values():
            if existing.dedupe_hash == candidate_hash:
                return True

        # Check against other candidates
        for existing in self._candidates_cache.values():
            existing_content = f"{existing.what}|{existing.why}|{'|'.join(sorted(existing.triggers))}"
            existing_hash = hashlib.sha256(existing_content.encode()).hexdigest()[:16]
            if existing_hash == candidate_hash:
                return True

        return False

    def extract_lessons_from_episodes(
        self,
        episodes: list[dict],
        run_id: str,
        benchmark: str,
        solver: str
    ) -> list[CandidateLesson]:
        """Extract candidate lessons from a batch of episodes.

        This is the main entry point for lesson extraction after an evaluation run.

        Args:
            episodes: List of episode dictionaries
            run_id: ID of the evaluation run
            benchmark: Benchmark name
            solver: Solver name

        Returns:
            List of extracted CandidateLessons
        """
        if not episodes:
            return []

        # Focus on failed episodes (more signal)
        failed_episodes = [
            e for e in episodes
            if not e.get("outcome", {}).get("passed", False)
        ]

        # Also include some successful episodes for positive patterns
        passed_episodes = [
            e for e in episodes
            if e.get("outcome", {}).get("passed", False)
        ]

        # Sample if too many
        if len(failed_episodes) > 10:
            import random
            failed_episodes = random.sample(failed_episodes, 10)
        if len(passed_episodes) > 5:
            import random
            passed_episodes = random.sample(passed_episodes, 5)

        analysis_episodes = failed_episodes + passed_episodes

        if not analysis_episodes:
            return []

        # Generate unique lesson ID prefix
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

        # For now, do simple pattern-based extraction without LLM
        # This can be upgraded to LLM-based extraction later
        candidates = self._extract_pattern_based(
            analysis_episodes,
            timestamp,
            benchmark,
            solver
        )

        # Deduplicate
        unique_candidates = []
        for candidate in candidates:
            if not self._is_duplicate(candidate):
                self.save_candidate(candidate)
                unique_candidates.append(candidate)

        return unique_candidates

    def _extract_pattern_based(
        self,
        episodes: list[dict],
        timestamp: str,
        benchmark: str,
        solver: str
    ) -> list[CandidateLesson]:
        """Extract lessons using pattern matching (non-LLM fallback).

        Analyzes failure modes and extracts simple lessons.
        """
        candidates = []

        # Analyze failure modes
        failure_counts: dict[str, int] = {}
        for ep in episodes:
            outcome = ep.get("outcome", {})
            if not outcome.get("passed", False):
                mode = outcome.get("failure_mode", "unknown")
                failure_counts[mode] = failure_counts.get(mode, 0) + 1

        # Generate lessons for common failure modes
        total_failures = sum(failure_counts.values())

        for mode, count in failure_counts.items():
            if count < 2 or total_failures == 0:
                continue

            proportion = count / total_failures
            if proportion < 0.2:  # At least 20% of failures
                continue

            lesson = self._lesson_for_failure_mode(
                mode,
                count,
                proportion,
                timestamp,
                benchmark,
                solver,
                [ep["sample_id"] for ep in episodes if ep.get("outcome", {}).get("failure_mode") == mode]
            )
            if lesson:
                candidates.append(lesson)

        return candidates

    def _lesson_for_failure_mode(
        self,
        mode: str,
        count: int,
        proportion: float,
        timestamp: str,
        benchmark: str,
        solver: str,
        episode_ids: list[str]
    ) -> Optional[CandidateLesson]:
        """Generate a lesson for a specific failure mode."""

        lessons_by_mode = {
            "wrong_answer": CandidateLesson(
                lesson_id=f"lesson_{timestamp}_wrong_answer",
                episode_ids=episode_ids[:5],  # Limit evidence
                what="Verify answer format matches expected output before submitting",
                why=f"Wrong answer was the dominant failure mode ({proportion:.0%} of failures)",
                expected="Reduce format mismatches and calculation errors",
                triggers=["final answer", "output formatting", benchmark],
                confidence=min(0.6 + proportion * 0.3, 0.9),
                source_benchmark=benchmark,
                source_solver=solver,
            ),
            "timeout": CandidateLesson(
                lesson_id=f"lesson_{timestamp}_timeout",
                episode_ids=episode_ids[:5],
                what="Set explicit reasoning limits and check progress periodically",
                why=f"Timeouts accounted for {proportion:.0%} of failures",
                expected="Reduce time-limit failures through better resource management",
                triggers=["complex problem", "multi-step reasoning", benchmark],
                confidence=min(0.5 + proportion * 0.4, 0.85),
                source_benchmark=benchmark,
                source_solver=solver,
            ),
            "crash": CandidateLesson(
                lesson_id=f"lesson_{timestamp}_crash",
                episode_ids=episode_ids[:5],
                what="Validate tool inputs and handle errors gracefully",
                why=f"Crashes represented {proportion:.0%} of failures",
                expected="Reduce unexpected errors through better error handling",
                triggers=["tool use", "external API", benchmark],
                confidence=min(0.5 + proportion * 0.3, 0.8),
                source_benchmark=benchmark,
                source_solver=solver,
            ),
            "cost_limit": CandidateLesson(
                lesson_id=f"lesson_{timestamp}_cost",
                episode_ids=episode_ids[:5],
                what="Be concise in reasoning and avoid unnecessary elaboration",
                why=f"Cost limits hit in {proportion:.0%} of failures",
                expected="Stay within token budgets through efficiency",
                triggers=["long problem", "complex reasoning", benchmark],
                confidence=min(0.5 + proportion * 0.35, 0.85),
                source_benchmark=benchmark,
                source_solver=solver,
            ),
        }

        return lessons_by_mode.get(mode)

    def retrieve_relevant_lessons(
        self,
        context: str,
        benchmark: Optional[str] = None,
        max_lessons: int = 5
    ) -> list[LessonCard]:
        """Retrieve lessons relevant to a given context.

        Uses trigger matching for now. Can be upgraded to semantic search.

        Args:
            context: Problem context or description
            benchmark: Optional benchmark to filter by
            max_lessons: Maximum lessons to return

        Returns:
            List of relevant LessonCards
        """
        if not self._lessons_cache:
            self.load_lessons()

        scored_lessons = []
        context_lower = context.lower()

        for lesson in self._lessons_cache.values():
            if lesson.status == "archived":
                continue

            score = 0.0

            # Check trigger matches
            for trigger in lesson.triggers:
                if trigger.lower() in context_lower:
                    score += 0.3

            # Boost for same benchmark
            if benchmark and lesson.source_benchmark == benchmark:
                score += 0.2

            # Factor in confidence and success rate
            score *= lesson.confidence
            if lesson.application_count > 0:
                score *= (0.5 + 0.5 * lesson.success_rate)

            if score > 0:
                scored_lessons.append((score, lesson))

        # Sort by score descending
        scored_lessons.sort(key=lambda x: -x[0])

        return [lesson for _, lesson in scored_lessons[:max_lessons]]

    def format_lessons_for_prompt(
        self,
        lessons: list[LessonCard],
        max_chars: int = 1000
    ) -> str:
        """Format lessons for injection into a prompt.

        Args:
            lessons: Lessons to format
            max_chars: Maximum characters to use

        Returns:
            Formatted string for prompt injection
        """
        if not lessons:
            return ""

        formatted = ["<lessons>"]
        chars_used = 10  # "<lessons>" tag

        for lesson in lessons:
            line = lesson.format_for_injection()
            if chars_used + len(line) + 2 > max_chars:
                break
            formatted.append(line)
            chars_used += len(line) + 1

        formatted.append("</lessons>")

        return "\n".join(formatted)

    def get_statistics(self) -> dict:
        """Get learning system statistics.

        Returns:
            Dictionary with statistics
        """
        if not self._lessons_cache:
            self.load_lessons()
        if not self._candidates_cache:
            self.load_candidates()

        lessons = list(self._lessons_cache.values())
        candidates = list(self._candidates_cache.values())

        return {
            "total_lessons": len(lessons),
            "total_candidates": len(candidates),
            "approved_lessons": len([l for l in lessons if l.status == "approved"]),
            "embedded_lessons": len([l for l in lessons if l.status == "embedded"]),
            "archived_lessons": len([l for l in lessons if l.status == "archived"]),
            "avg_confidence": sum(l.confidence for l in lessons) / len(lessons) if lessons else 0,
            "avg_success_rate": sum(l.success_rate for l in lessons if l.application_count > 0) /
                               max(1, len([l for l in lessons if l.application_count > 0])),
            "total_applications": sum(l.application_count for l in lessons),
        }

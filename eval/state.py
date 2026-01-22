"""State machine and data models for evaluation runs."""

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Literal, Any


# Pricing per 1M tokens (approximate)
MODEL_PRICING = {
    "anthropic/claude-sonnet-4-20250514": {"input": 3.0, "output": 15.0},
    "anthropic/claude-opus-4-5-20251101": {"input": 15.0, "output": 75.0},
    "openai/gpt-4o": {"input": 2.5, "output": 10.0},
    "openai/gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "google/gemini-2.0-flash": {"input": 0.075, "output": 0.30},
    # Default fallback
    "default": {"input": 3.0, "output": 15.0},
}


def calculate_cost(
    input_tokens: int,
    output_tokens: int,
    model: str = "default"
) -> dict:
    """Calculate cost in USD from token counts."""
    pricing = MODEL_PRICING.get(model, MODEL_PRICING["default"])
    input_cost = (input_tokens / 1_000_000) * pricing["input"]
    output_cost = (output_tokens / 1_000_000) * pricing["output"]
    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "usd": round(input_cost + output_cost, 6),
    }


@dataclass
class Episode:
    """A single evaluation sample with 4-tuple logging."""
    sample_id: str
    context: dict  # input, target, metadata
    traces: list[dict]  # model/tool events
    action: dict  # output, tool_calls_count
    outcome: dict  # passed, score, failure_mode
    cost: dict  # input_tokens, output_tokens, usd
    run_id: Optional[str] = None
    timestamp: Optional[str] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(asdict(self), indent=2)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Episode":
        """Create Episode from dictionary."""
        return cls(**data)

    def save(self, path: Path):
        """Save episode to file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.to_json())


@dataclass
class RunConfig:
    """Configuration for an evaluation run."""
    benchmark: str
    solver: str
    model: str
    samples: Optional[int] = None  # None = all samples
    timeout_per_sample: int = 300  # seconds

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class RunSummary:
    """Summary statistics for a completed run."""
    run_id: str
    benchmark: str
    solver: str
    total_samples: int
    passed: int
    failed: int
    pass_rate: float
    total_cost_usd: float
    total_duration_seconds: float = 0.0
    pass_rate_ci_95: Optional[tuple[float, float]] = None
    failure_modes: Optional[dict[str, int]] = None

    @property
    def cost_per_success(self) -> float:
        """Cost per successfully solved sample."""
        if self.passed == 0:
            return float("inf")
        return self.total_cost_usd / self.passed

    def to_dict(self) -> dict:
        data = asdict(self)
        data["cost_per_success"] = self.cost_per_success
        return data

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


EvalPhase = Literal["IDLE", "SETUP", "RUNNING", "ANALYZING", "LEARNING"]


@dataclass
class EvalState:
    """Persistent state for evaluation workflow."""
    phase: EvalPhase = "IDLE"
    current_run_id: Optional[str] = None
    current_benchmark: Optional[str] = None
    current_solver: Optional[str] = None
    samples_completed: int = 0
    samples_total: int = 0
    last_updated: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def start_run(self, run_id: str, benchmark: str, solver: str, total_samples: int = 0):
        """Start a new evaluation run."""
        self.phase = "RUNNING"
        self.current_run_id = run_id
        self.current_benchmark = benchmark
        self.current_solver = solver
        self.samples_completed = 0
        self.samples_total = total_samples
        self.last_updated = datetime.now(timezone.utc).isoformat()

    def complete_sample(self):
        """Mark one sample as complete."""
        self.samples_completed += 1
        self.last_updated = datetime.now(timezone.utc).isoformat()

    def finish_run(self):
        """Mark run as complete."""
        self.phase = "IDLE"
        self.last_updated = datetime.now(timezone.utc).isoformat()

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(asdict(self), indent=2)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_json(cls, json_str: str) -> "EvalState":
        """Load from JSON string."""
        data = json.loads(json_str)
        return cls(**data)

    def save(self, path: Path):
        """Save state to file."""
        path.write_text(self.to_json())

    @classmethod
    def load(cls, path: Path) -> "EvalState":
        """Load state from file."""
        if not path.exists():
            return cls()
        return cls.from_json(path.read_text())

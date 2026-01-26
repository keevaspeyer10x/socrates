"""Rubric definition and loading for LLM-as-Judge evaluation.

Rubrics define the criteria used to evaluate open-ended responses.
They are stored as YAML files for easy customization and versioning.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
import yaml


@dataclass
class Criterion:
    """A single evaluation criterion with scoring anchors.

    Attributes:
        name: Short identifier (e.g., "novelty", "depth")
        description: What this criterion measures
        weight: Relative importance (0.0 to 1.0, should sum to 1.0 across criteria)
        anchors: Score anchors mapping score -> description
    """
    name: str
    description: str
    weight: float = 0.25
    anchors: dict[int, str] = field(default_factory=dict)

    def format_anchors(self) -> str:
        """Format anchors for inclusion in judge prompt."""
        lines = []
        for score in sorted(self.anchors.keys()):
            lines.append(f"  {score}: {self.anchors[score]}")
        return "\n".join(lines)


@dataclass
class Rubric:
    """Complete rubric for evaluating open-ended responses.

    Attributes:
        name: Rubric identifier (e.g., "reasoning", "creative")
        version: Rubric version for tracking changes
        description: What this rubric is designed to evaluate
        criteria: List of evaluation criteria
        scale_min: Minimum score value
        scale_max: Maximum score value
        instructions: Additional instructions for the judge
    """
    name: str
    version: str
    description: str
    criteria: list[Criterion]
    scale_min: int = 1
    scale_max: int = 5
    instructions: str = ""

    def __post_init__(self):
        """Validate rubric after initialization."""
        # Check weights sum to approximately 1.0
        total_weight = sum(c.weight for c in self.criteria)
        if abs(total_weight - 1.0) > 0.01:
            # Normalize weights
            for c in self.criteria:
                c.weight = c.weight / total_weight

    def format_for_prompt(self) -> str:
        """Format rubric as text for inclusion in judge prompt."""
        lines = [
            f"# Evaluation Rubric: {self.name} (v{self.version})",
            f"\n{self.description}\n",
            f"Score each criterion on a scale of {self.scale_min} to {self.scale_max}.\n",
            "## Criteria:\n",
        ]

        for criterion in self.criteria:
            lines.append(f"### {criterion.name} (weight: {criterion.weight:.0%})")
            lines.append(f"{criterion.description}\n")
            if criterion.anchors:
                lines.append("Score anchors:")
                lines.append(criterion.format_anchors())
            lines.append("")

        if self.instructions:
            lines.append(f"## Additional Instructions:\n{self.instructions}")

        return "\n".join(lines)

    def to_dict(self) -> dict:
        """Convert to dictionary for YAML serialization."""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "scale_min": self.scale_min,
            "scale_max": self.scale_max,
            "instructions": self.instructions,
            "criteria": [
                {
                    "name": c.name,
                    "description": c.description,
                    "weight": c.weight,
                    "anchors": c.anchors,
                }
                for c in self.criteria
            ],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Rubric":
        """Create Rubric from dictionary."""
        criteria = [
            Criterion(
                name=c["name"],
                description=c["description"],
                weight=c.get("weight", 0.25),
                anchors=c.get("anchors", {}),
            )
            for c in data.get("criteria", [])
        ]

        return cls(
            name=data["name"],
            version=data.get("version", "1.0.0"),
            description=data.get("description", ""),
            criteria=criteria,
            scale_min=data.get("scale_min", 1),
            scale_max=data.get("scale_max", 5),
            instructions=data.get("instructions", ""),
        )


def load_rubric(path: Path | str) -> Rubric:
    """Load a rubric from a YAML file.

    Args:
        path: Path to YAML rubric file

    Returns:
        Loaded Rubric instance

    Raises:
        FileNotFoundError: If rubric file doesn't exist
        ValueError: If rubric is invalid
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Rubric file not found: {path}")

    with open(path) as f:
        data = yaml.safe_load(f)

    return Rubric.from_dict(data)


def save_rubric(rubric: Rubric, path: Path | str) -> None:
    """Save a rubric to a YAML file.

    Args:
        rubric: Rubric to save
        path: Output path for YAML file
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w") as f:
        yaml.dump(rubric.to_dict(), f, default_flow_style=False, sort_keys=False)


# Default rubrics for common use cases
DEFAULT_REASONING_RUBRIC = Rubric(
    name="reasoning",
    version="1.0.0",
    description="Evaluate the quality of open-ended reasoning and analysis.",
    criteria=[
        Criterion(
            name="depth",
            description="How thoroughly does the response explore the problem? Does it consider root causes, implications, and edge cases?",
            weight=0.30,
            anchors={
                1: "Surface-level only, misses key aspects",
                2: "Basic exploration, some aspects addressed",
                3: "Adequate depth, covers main points",
                4: "Thorough analysis with good coverage",
                5: "Exceptional depth, explores subtle implications",
            },
        ),
        Criterion(
            name="coherence",
            description="Is the reasoning logically structured and internally consistent? Does it flow well?",
            weight=0.25,
            anchors={
                1: "Disjointed, contradictory",
                2: "Some logical gaps or inconsistencies",
                3: "Generally coherent with minor issues",
                4: "Well-structured and consistent",
                5: "Exceptionally clear and logical flow",
            },
        ),
        Criterion(
            name="practicality",
            description="Are the conclusions actionable? Does the response consider real-world constraints?",
            weight=0.25,
            anchors={
                1: "Impractical or ignores constraints",
                2: "Limited practicality",
                3: "Reasonably actionable",
                4: "Highly practical with clear steps",
                5: "Immediately actionable with excellent feasibility",
            },
        ),
        Criterion(
            name="novelty",
            description="Does the response offer original insights or unexpected connections?",
            weight=0.20,
            anchors={
                1: "Entirely conventional",
                2: "Mostly standard with minor insights",
                3: "Some original thinking",
                4: "Notable creative elements",
                5: "Highly original and insightful",
            },
        ),
    ],
    instructions="Focus on the quality of reasoning, not just correctness. A well-reasoned wrong answer may score higher on some criteria than a correct but shallow answer.",
)


DEFAULT_DEBATE_RUBRIC = Rubric(
    name="debate",
    version="1.0.0",
    description="Evaluate debate-style reasoning with multiple perspectives.",
    criteria=[
        Criterion(
            name="perspective_coverage",
            description="How well does the response consider multiple viewpoints and perspectives?",
            weight=0.25,
            anchors={
                1: "Single perspective only",
                2: "Acknowledges alternatives superficially",
                3: "Explores 2-3 perspectives adequately",
                4: "Thorough multi-perspective analysis",
                5: "Comprehensive coverage of diverse viewpoints",
            },
        ),
        Criterion(
            name="argument_quality",
            description="How strong and well-supported are the arguments presented?",
            weight=0.25,
            anchors={
                1: "Weak, unsupported claims",
                2: "Some evidence but gaps in reasoning",
                3: "Reasonably supported arguments",
                4: "Strong arguments with good evidence",
                5: "Compelling, well-evidenced arguments",
            },
        ),
        Criterion(
            name="synthesis",
            description="How well does the response synthesize different viewpoints into a coherent conclusion?",
            weight=0.30,
            anchors={
                1: "No synthesis, just listing",
                2: "Superficial reconciliation",
                3: "Adequate integration of perspectives",
                4: "Thoughtful synthesis with nuance",
                5: "Masterful integration creating new insights",
            },
        ),
        Criterion(
            name="intellectual_honesty",
            description="Does the response acknowledge uncertainty, limitations, and counterarguments fairly?",
            weight=0.20,
            anchors={
                1: "Overconfident, ignores counterarguments",
                2: "Some acknowledgment of limitations",
                3: "Fair treatment of opposing views",
                4: "Honest about uncertainty and limitations",
                5: "Exemplary epistemic humility and fairness",
            },
        ),
    ],
    instructions="Evaluate the quality of deliberation, not the specific conclusion reached. Good debate should steelman opposing views.",
)

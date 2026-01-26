"""Pairwise comparison scorer for A/B evaluation of responses.

Compares two responses head-to-head with blinding and order randomization
to determine which is better according to specified criteria.
"""

import json
import random
import re
from typing import Optional

from .rubric import Rubric, DEFAULT_REASONING_RUBRIC, Criterion


PAIRWISE_SYSTEM_PROMPT = """You are an expert evaluator comparing two AI-generated responses.
Your task is to determine which response is better according to specific criteria.

IMPORTANT:
- The responses are labeled "Response A" and "Response B" - their order is randomized
- Do NOT be biased toward either label
- Focus on substance over style or length
- Cite specific evidence to justify your choice

{criteria_description}

## Output Format

You MUST respond with a valid JSON object in exactly this format:
```json
{{
  "winner": "<A or B or TIE>",
  "criteria_verdicts": {{
    "<criterion_name>": {{
      "winner": "<A or B or TIE>",
      "explanation": "<brief explanation>"
    }}
  }},
  "overall_explanation": "<1-2 sentence summary of why the winner is better>",
  "confidence": <float 0.0-1.0>
}}
```"""


PAIRWISE_USER_PROMPT = """## Question/Prompt Given to AI:
{prompt}

## Response A:
{response_a}

## Response B:
{response_b}

Compare these responses according to the criteria. Which is better overall? Provide your assessment as a JSON object."""


def parse_pairwise_response(response_text: str) -> Optional[dict]:
    """Parse the JSON response from the pairwise comparison.

    Args:
        response_text: Raw text response from judge

    Returns:
        Parsed dictionary or None if parsing fails
    """
    # Try to extract JSON from markdown code fence
    json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    # Try to find raw JSON object
    json_match = re.search(r'\{[^{}]*"winner"[^{}]*\}', response_text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError:
            pass

    # Try entire response
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        return None


class PairwiseScorer:
    """Pairwise comparison scorer for A/B evaluation.

    Compares two responses with order randomization to control for
    position bias. Can use a rubric's criteria or custom criteria.
    """

    def __init__(
        self,
        rubric: Optional[Rubric] = None,
        judge_model: str = "anthropic/claude-opus-4-5-20251101",
        randomize_order: bool = True,
    ):
        """Initialize PairwiseScorer.

        Args:
            rubric: Rubric to use for criteria (defaults to reasoning)
            judge_model: Model to use as judge
            randomize_order: Whether to randomize response order
        """
        self.rubric = rubric or DEFAULT_REASONING_RUBRIC
        self.judge_model = judge_model
        self.randomize_order = randomize_order
        self._model = None

    async def _get_model(self):
        """Get or create the judge model instance."""
        if self._model is None:
            from inspect_ai.model import get_model
            self._model = get_model(self.judge_model)
        return self._model

    def _format_criteria(self) -> str:
        """Format criteria description for the prompt."""
        lines = ["## Evaluation Criteria:"]
        for criterion in self.rubric.criteria:
            lines.append(f"\n### {criterion.name}")
            lines.append(criterion.description)
        return "\n".join(lines)

    async def compare(
        self,
        prompt: str,
        response_1: str,
        response_2: str,
        label_1: str = "Response 1",
        label_2: str = "Response 2",
    ) -> dict:
        """Compare two responses and determine the winner.

        Args:
            prompt: The original prompt/question
            response_1: First response
            response_2: Second response
            label_1: Label for first response (for tracking)
            label_2: Label for second response (for tracking)

        Returns:
            Dictionary with:
                - winner: "response_1", "response_2", or "tie"
                - winner_label: Original label of winner
                - criteria_verdicts: Per-criterion winners
                - explanation: Why the winner is better
                - confidence: Judge's confidence
                - order_was_swapped: Whether order was randomized
        """
        from inspect_ai.model import ChatMessageSystem, ChatMessageUser

        model = await self._get_model()

        # Optionally randomize order to control for position bias
        if self.randomize_order:
            swap = random.choice([True, False])
        else:
            swap = False

        if swap:
            response_a, response_b = response_2, response_1
            label_a, label_b = label_2, label_1
        else:
            response_a, response_b = response_1, response_2
            label_a, label_b = label_1, label_2

        # Build prompt
        system_prompt = PAIRWISE_SYSTEM_PROMPT.format(
            criteria_description=self._format_criteria()
        )
        user_prompt = PAIRWISE_USER_PROMPT.format(
            prompt=prompt,
            response_a=response_a,
            response_b=response_b,
        )

        # Query judge
        messages = [
            ChatMessageSystem(content=system_prompt),
            ChatMessageUser(content=user_prompt),
        ]

        judge_response = await model.generate(messages)

        # Extract text
        if hasattr(judge_response, 'completion'):
            response_text = judge_response.completion
        elif hasattr(judge_response, 'message') and hasattr(judge_response.message, 'content'):
            response_text = str(judge_response.message.content)
        else:
            response_text = str(judge_response)

        # Parse response
        parsed = parse_pairwise_response(response_text)

        if parsed is None:
            return {
                "winner": "tie",
                "winner_label": None,
                "criteria_verdicts": {},
                "explanation": "Failed to parse judge response",
                "confidence": 0.0,
                "order_was_swapped": swap,
                "raw_response": response_text,
                "parse_error": True,
            }

        # Map winner back to original order
        raw_winner = parsed.get("winner", "TIE").upper()

        if raw_winner == "A":
            winner = "response_2" if swap else "response_1"
            winner_label = label_a
        elif raw_winner == "B":
            winner = "response_1" if swap else "response_2"
            winner_label = label_b
        else:
            winner = "tie"
            winner_label = None

        # Map criteria verdicts back to original order
        criteria_verdicts = {}
        for criterion, verdict in parsed.get("criteria_verdicts", {}).items():
            crit_winner = verdict.get("winner", "TIE").upper()
            if crit_winner == "A":
                mapped_winner = label_a
            elif crit_winner == "B":
                mapped_winner = label_b
            else:
                mapped_winner = "tie"

            criteria_verdicts[criterion] = {
                "winner": mapped_winner,
                "explanation": verdict.get("explanation", ""),
            }

        return {
            "winner": winner,
            "winner_label": winner_label,
            "criteria_verdicts": criteria_verdicts,
            "explanation": parsed.get("overall_explanation", ""),
            "confidence": parsed.get("confidence", 1.0),
            "order_was_swapped": swap,
            "raw_response": response_text,
        }


def pairwise_scorer(
    baseline_response_key: str = "baseline_response",
    rubric: Optional[Rubric] = None,
    judge_model: str = "anthropic/claude-opus-4-5-20251101",
):
    """Create an inspect_ai scorer for pairwise comparison.

    Compares the model's response against a baseline response stored
    in the sample metadata.

    Args:
        baseline_response_key: Key in sample metadata for baseline response
        rubric: Evaluation rubric (defaults to reasoning)
        judge_model: Model to use as judge

    Returns:
        Inspect AI scorer function
    """
    from inspect_ai.scorer import Score, scorer, accuracy, CORRECT, INCORRECT

    comparer = PairwiseScorer(
        rubric=rubric,
        judge_model=judge_model,
        randomize_order=True,
    )

    @scorer(metrics=[accuracy()])
    def _pairwise_scorer():
        async def do_score(state, target) -> Score:
            """Score a sample via pairwise comparison."""
            # Extract prompt
            prompt = ""
            if hasattr(state, 'input'):
                prompt = str(state.input)
            elif hasattr(state, 'messages') and state.messages:
                for msg in state.messages:
                    if hasattr(msg, 'role') and msg.role == 'user':
                        prompt = str(msg.content)
                        break

            # Extract model response
            model_response = ""
            if hasattr(state, 'output') and state.output:
                model_response = str(
                    state.output.completion if hasattr(state.output, 'completion')
                    else state.output
                )

            # Get baseline from metadata
            metadata = {}
            if hasattr(state, 'metadata'):
                metadata = state.metadata or {}

            baseline_response = metadata.get(baseline_response_key, "")
            if not baseline_response:
                return Score(
                    value=INCORRECT,
                    explanation=f"No baseline response in metadata['{baseline_response_key}']",
                )

            # Compare
            result = await comparer.compare(
                prompt=prompt,
                response_1=model_response,
                response_2=baseline_response,
                label_1="model",
                label_2="baseline",
            )

            # Model wins if it beats baseline
            if result["winner"] == "response_1":
                value = CORRECT
            elif result["winner"] == "tie":
                value = INCORRECT  # Tie doesn't beat baseline
            else:
                value = INCORRECT

            return Score(
                value=value,
                answer=model_response[:500],
                explanation=result["explanation"],
                metadata={
                    "winner": result["winner"],
                    "winner_label": result["winner_label"],
                    "criteria_verdicts": result["criteria_verdicts"],
                    "confidence": result["confidence"],
                    "order_was_swapped": result["order_was_swapped"],
                },
            )

        return do_score

    return _pairwise_scorer()

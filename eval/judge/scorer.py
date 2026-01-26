"""JudgeScorer - LLM-as-Judge scorer for inspect_ai integration.

Evaluates open-ended responses using an LLM judge with a rubric.
Returns structured scores with justifications.
"""

import json
import re
from typing import Any, Optional

from .rubric import Rubric, DEFAULT_REASONING_RUBRIC


JUDGE_SYSTEM_PROMPT = """You are an expert evaluator assessing the quality of AI-generated responses.
Your task is to evaluate responses based on a specific rubric with defined criteria.

Be objective and consistent in your scoring. Cite specific evidence from the response to justify your scores.
Do not be swayed by verbosity - longer responses are not necessarily better.
Focus on substance over style.

{rubric}

## Output Format

You MUST respond with a valid JSON object in exactly this format:
```json
{{
  "scores": {{
    "<criterion_name>": {{
      "score": <integer>,
      "justification": "<brief explanation citing evidence>"
    }}
  }},
  "overall_assessment": "<1-2 sentence summary>",
  "suggestions": ["<optional improvement suggestion>"],
  "confidence": <float 0.0-1.0>
}}
```

Replace <criterion_name> with the actual criterion names from the rubric."""


JUDGE_USER_PROMPT = """## Question/Prompt Given to AI:
{prompt}

## AI Response to Evaluate:
{response}

Evaluate this response according to the rubric. Provide your assessment as a JSON object."""


def parse_judge_response(response_text: str) -> Optional[dict]:
    """Parse the JSON response from the judge model.

    Args:
        response_text: Raw text response from judge

    Returns:
        Parsed dictionary or None if parsing fails
    """
    # Try to extract JSON from the response
    # Look for JSON block in markdown code fence
    json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    # Try to find raw JSON object
    json_match = re.search(r'\{[^{}]*"scores"[^{}]*\{.*\}.*\}', response_text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError:
            pass

    # Last resort: try to parse entire response as JSON
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        return None


def calculate_weighted_score(
    scores: dict[str, dict],
    rubric: Rubric
) -> float:
    """Calculate weighted score from individual criterion scores.

    Args:
        scores: Dict of criterion_name -> {score, justification}
        rubric: Rubric with criterion weights

    Returns:
        Weighted score normalized to 0.0-1.0 range
    """
    total_score = 0.0
    total_weight = 0.0

    for criterion in rubric.criteria:
        if criterion.name in scores:
            score_data = scores[criterion.name]
            raw_score = score_data.get("score", rubric.scale_min)

            # Normalize to 0-1 range
            normalized = (raw_score - rubric.scale_min) / (rubric.scale_max - rubric.scale_min)

            total_score += normalized * criterion.weight
            total_weight += criterion.weight

    if total_weight == 0:
        return 0.0

    return total_score / total_weight


class JudgeScorer:
    """LLM-as-Judge scorer for evaluating open-ended responses.

    Uses a specified LLM model to evaluate responses according to a rubric,
    producing structured scores with justifications.
    """

    def __init__(
        self,
        rubric: Optional[Rubric] = None,
        judge_model: str = "anthropic/claude-opus-4-5-20251101",
        pass_threshold: float = 0.6,
    ):
        """Initialize JudgeScorer.

        Args:
            rubric: Evaluation rubric (defaults to reasoning rubric)
            judge_model: Model to use as judge
            pass_threshold: Minimum weighted score to pass (0.0-1.0)
        """
        self.rubric = rubric or DEFAULT_REASONING_RUBRIC
        self.judge_model = judge_model
        self.pass_threshold = pass_threshold
        self._model = None

    async def _get_model(self):
        """Get or create the judge model instance."""
        if self._model is None:
            from inspect_ai.model import get_model
            self._model = get_model(self.judge_model)
        return self._model

    async def score(
        self,
        prompt: str,
        response: str,
    ) -> dict:
        """Score a single response using the judge model.

        Args:
            prompt: The original prompt/question
            response: The AI response to evaluate

        Returns:
            Dictionary with:
                - scores: Per-criterion scores and justifications
                - weighted_score: Overall weighted score (0.0-1.0)
                - passed: Whether response meets threshold
                - overall_assessment: Summary from judge
                - confidence: Judge's confidence in assessment
                - raw_response: Raw judge output for debugging
        """
        from inspect_ai.model import ChatMessageSystem, ChatMessageUser

        model = await self._get_model()

        # Build judge prompt
        system_prompt = JUDGE_SYSTEM_PROMPT.format(
            rubric=self.rubric.format_for_prompt()
        )
        user_prompt = JUDGE_USER_PROMPT.format(
            prompt=prompt,
            response=response
        )

        # Query judge model
        messages = [
            ChatMessageSystem(content=system_prompt),
            ChatMessageUser(content=user_prompt),
        ]

        judge_response = await model.generate(messages)

        # Extract text from response
        if hasattr(judge_response, 'completion'):
            response_text = judge_response.completion
        elif hasattr(judge_response, 'message') and hasattr(judge_response.message, 'content'):
            response_text = str(judge_response.message.content)
        else:
            response_text = str(judge_response)

        # Parse judge response
        parsed = parse_judge_response(response_text)

        if parsed is None:
            # Failed to parse - return error result
            return {
                "scores": {},
                "weighted_score": 0.0,
                "passed": False,
                "overall_assessment": "Failed to parse judge response",
                "confidence": 0.0,
                "raw_response": response_text,
                "parse_error": True,
            }

        # Calculate weighted score
        scores = parsed.get("scores", {})
        weighted_score = calculate_weighted_score(scores, self.rubric)

        return {
            "scores": scores,
            "weighted_score": weighted_score,
            "passed": weighted_score >= self.pass_threshold,
            "overall_assessment": parsed.get("overall_assessment", ""),
            "suggestions": parsed.get("suggestions", []),
            "confidence": parsed.get("confidence", 1.0),
            "raw_response": response_text,
        }


def judge_scorer(
    rubric: Optional[Rubric] = None,
    judge_model: str = "anthropic/claude-opus-4-5-20251101",
    pass_threshold: float = 0.6,
):
    """Create an inspect_ai scorer using LLM-as-Judge evaluation.

    Args:
        rubric: Evaluation rubric (defaults to reasoning rubric)
        judge_model: Model to use as judge
        pass_threshold: Minimum weighted score to pass (0.0-1.0)

    Returns:
        Inspect AI scorer function
    """
    from inspect_ai.scorer import Score, scorer, accuracy, CORRECT, INCORRECT

    judge = JudgeScorer(
        rubric=rubric,
        judge_model=judge_model,
        pass_threshold=pass_threshold,
    )

    @scorer(metrics=[accuracy()])
    def _judge_scorer():
        async def do_score(state, target) -> Score:
            """Score a sample using the judge."""
            # Extract prompt from state
            prompt = ""
            if hasattr(state, 'input'):
                prompt = str(state.input)
            elif hasattr(state, 'messages') and state.messages:
                # Get first user message as prompt
                for msg in state.messages:
                    if hasattr(msg, 'role') and msg.role == 'user':
                        prompt = str(msg.content)
                        break

            # Extract response from state
            response = ""
            if hasattr(state, 'output') and state.output:
                response = str(state.output.completion if hasattr(state.output, 'completion') else state.output)

            # Score using judge
            result = await judge.score(prompt, response)

            # Return inspect_ai Score
            value = CORRECT if result["passed"] else INCORRECT

            return Score(
                value=value,
                answer=response[:500],  # Truncate for logging
                explanation=result["overall_assessment"],
                metadata={
                    "scores": result["scores"],
                    "weighted_score": result["weighted_score"],
                    "confidence": result["confidence"],
                    "suggestions": result.get("suggestions", []),
                    "rubric": judge.rubric.name,
                    "judge_model": judge.judge_model,
                },
            )

        return do_score

    return _judge_scorer()

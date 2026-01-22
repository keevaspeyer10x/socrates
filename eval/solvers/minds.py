"""MindsSolver - Multi-model collaboration solver for evaluation.

Queries multiple AI models in parallel, then synthesizes their responses
into a single answer using Claude as the synthesizer.

Supports model fallbacks (LEARNINGS recommendation) - when a primary model
fails, the solver can automatically try a fallback model.
"""

import asyncio
from typing import Any, Optional

from .base import Solver
from ..rate_limiter import RateLimiter


# Default models from multiminds (top 5)
DEFAULT_MODELS = [
    "anthropic/claude-opus-4-5-20251101",    # Claude Opus 4.5
    "google/gemini-3-pro-preview",            # Gemini 3 Pro
    "openai/gpt-5.2",                         # GPT-5.2
    "x-ai/grok-4.1-fast",                     # Grok 4.1
    "deepseek/deepseek-v3.2",                 # DeepSeek V3.2
]

# Default synthesizer model
DEFAULT_SYNTHESIZER = "anthropic/claude-opus-4-5-20251101"

# Model fallbacks for when primary models are unavailable (LEARNINGS recommendation)
# Maps primary model to fallback(s)
DEFAULT_FALLBACKS: dict[str, list[str]] = {
    "anthropic/claude-opus-4-5-20251101": ["anthropic/claude-sonnet-4-20250514"],
    "google/gemini-3-pro-preview": ["google/gemini-2.0-flash"],
    "openai/gpt-5.2": ["openai/gpt-4o"],
    "x-ai/grok-4.1-fast": ["x-ai/grok-3"],
    "deepseek/deepseek-v3.2": ["deepseek/deepseek-v3"],
}


SYNTHESIS_PROMPT = """You are synthesizing responses from multiple AI models to produce the best possible answer.

## Responses from different models:

{responses}

## Task:
Based on the above responses:
1. Identify the consensus across models
2. Resolve any disagreements by evaluating the reasoning
3. Extract the most accurate final answer

IMPORTANT: You MUST end your response with a line in exactly this format:
ANSWER: <your final answer>

For example: "ANSWER: 42" or "ANSWER: The capital is Paris"

## Your synthesized answer:"""


class MindsSolver(Solver):
    """Multi-model collaboration solver.

    Queries multiple AI models in parallel, applies rate limiting,
    and synthesizes responses using Claude. Supports model fallbacks
    when primary models are unavailable.
    """

    name = "minds"

    def __init__(
        self,
        models: Optional[list[str]] = None,
        synthesizer_model: str = DEFAULT_SYNTHESIZER,
        rate_limits: Optional[dict[str, int]] = None,
        fallbacks: Optional[dict[str, list[str]]] = None,
        use_fallbacks: bool = True,
    ):
        """Initialize MindsSolver.

        Args:
            models: List of model identifiers to query
            synthesizer_model: Model to use for synthesis
            rate_limits: Custom rate limits per provider
            fallbacks: Custom model fallback mapping (model -> [fallbacks])
            use_fallbacks: Whether to use fallbacks on model errors
        """
        self.models = models or DEFAULT_MODELS
        self.synthesizer_model = synthesizer_model
        self.rate_limiter = RateLimiter(provider_limits=rate_limits)
        self.fallbacks = fallbacks if fallbacks is not None else DEFAULT_FALLBACKS
        self.use_fallbacks = use_fallbacks
        self._model_cache: dict[str, Any] = {}
        self._fallback_stats: dict[str, int] = {}  # Track fallback usage

    @property
    def metadata(self) -> dict:
        """Return solver metadata for logging."""
        return {
            "name": self.name,
            "models": self.models,
            "synthesizer": self.synthesizer_model,
            "model_count": len(self.models),
            "use_fallbacks": self.use_fallbacks,
            "fallback_stats": self._fallback_stats,
        }

    async def _get_model(self, model_id: str):
        """Get or create an Inspect model instance.

        Uses caching to avoid recreating models.
        """
        if model_id not in self._model_cache:
            from inspect_ai.model import get_model
            self._model_cache[model_id] = get_model(model_id)
        return self._model_cache[model_id]

    async def _query_single_model(
        self,
        model_id: str,
        state: Any,
    ) -> str:
        """Query a single model (without fallback logic).

        Args:
            model_id: Model identifier
            state: Inspect TaskState

        Returns:
            Model response text

        Raises:
            Exception: If model query fails
        """
        # Apply rate limiting
        provider = self.rate_limiter.get_provider_from_model(model_id)
        await self.rate_limiter.acquire(provider)

        # Get the model
        model = await self._get_model(model_id)

        # Generate response
        messages = state.messages if hasattr(state, 'messages') else []
        response = await model.generate(messages)

        # Extract text from response
        if hasattr(response, 'completion'):
            return response.completion
        elif hasattr(response, 'message') and hasattr(response.message, 'content'):
            return str(response.message.content)
        return str(response)

    async def _query_model(
        self,
        model_id: str,
        state: Any,
        generate: Any
    ) -> tuple[str, str]:
        """Query a single model with rate limiting and fallback support.

        Args:
            model_id: Model identifier
            state: Inspect TaskState
            generate: Inspect generate function

        Returns:
            Tuple of (actual_model_used, response_text)
        """
        # Try primary model first
        try:
            response = await self._query_single_model(model_id, state)
            return (model_id, response)
        except Exception as primary_error:
            # If fallbacks disabled or no fallbacks configured, return error
            if not self.use_fallbacks or model_id not in self.fallbacks:
                return (model_id, f"[Error from {model_id}: {str(primary_error)[:200]}]")

            # Try fallbacks in order
            for fallback_model in self.fallbacks[model_id]:
                try:
                    response = await self._query_single_model(fallback_model, state)
                    # Track fallback usage
                    self._fallback_stats[fallback_model] = self._fallback_stats.get(fallback_model, 0) + 1
                    return (f"{fallback_model} (fallback for {model_id})", response)
                except Exception:
                    continue  # Try next fallback

            # All fallbacks failed
            return (model_id, f"[Error from {model_id} and all fallbacks: {str(primary_error)[:200]}]")

    async def _synthesize(
        self,
        state: Any,
        responses: list[tuple[str, str]],
        generate: Any
    ) -> Any:
        """Synthesize responses from all models.

        Args:
            state: Original TaskState
            responses: List of (model_id, response_text) tuples
            generate: Inspect generate function

        Returns:
            Updated TaskState with synthesized answer
        """
        # Format responses for synthesis
        formatted_responses = "\n\n".join([
            f"### {model_id}\n{response}"
            for model_id, response in responses
        ])

        synthesis_prompt = SYNTHESIS_PROMPT.format(responses=formatted_responses)

        # Apply rate limiting for synthesizer
        provider = self.rate_limiter.get_provider_from_model(self.synthesizer_model)
        await self.rate_limiter.acquire(provider)

        # Use the main generate function with synthesizer model
        # Create a modified state with the synthesis prompt
        from copy import deepcopy
        synth_state = deepcopy(state)

        # Add synthesis prompt to messages
        if hasattr(synth_state, 'messages'):
            from inspect_ai.model import ChatMessageUser
            synth_state.messages.append(ChatMessageUser(content=synthesis_prompt))

        # Generate synthesized response
        return await generate(synth_state)

    async def solve(self, state: Any, generate: Any) -> Any:
        """Generate solution using multi-model collaboration.

        Args:
            state: Inspect TaskState with input, messages, tools
            generate: Inspect generate function

        Returns:
            Updated TaskState with synthesized solution
        """
        # Query all models in parallel
        tasks = [
            self._query_model(model_id, state, generate)
            for model_id in self.models
        ]

        # Wait for all responses (with error handling)
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results - _query_model now returns (model_label, response_text)
        response_pairs = []
        for model_id, result in zip(self.models, results):
            if isinstance(result, Exception):
                response_pairs.append((model_id, f"[Error: {str(result)[:200]}]"))
            else:
                # result is (actual_model_label, response_text)
                response_pairs.append(result)

        # Synthesize responses
        return await self._synthesize(state, response_pairs, generate)

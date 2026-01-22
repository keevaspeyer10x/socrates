"""MindsSolver - Multi-model collaboration solver for evaluation.

Queries multiple AI models in parallel, then synthesizes their responses
into a single answer using Claude as the synthesizer.
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


SYNTHESIS_PROMPT = """You are synthesizing responses from multiple AI models to produce the best possible answer.

## Responses from different models:

{responses}

## Task:
Based on the above responses, provide a final synthesized answer that:
1. Identifies the consensus across models
2. Resolves any disagreements by evaluating the reasoning
3. Produces the most accurate and complete answer

## Your synthesized answer:"""


class MindsSolver(Solver):
    """Multi-model collaboration solver.

    Queries multiple AI models in parallel, applies rate limiting,
    and synthesizes responses using Claude.
    """

    name = "minds"

    def __init__(
        self,
        models: Optional[list[str]] = None,
        synthesizer_model: str = DEFAULT_SYNTHESIZER,
        rate_limits: Optional[dict[str, int]] = None,
    ):
        """Initialize MindsSolver.

        Args:
            models: List of model identifiers to query
            synthesizer_model: Model to use for synthesis
            rate_limits: Custom rate limits per provider
        """
        self.models = models or DEFAULT_MODELS
        self.synthesizer_model = synthesizer_model
        self.rate_limiter = RateLimiter(provider_limits=rate_limits)
        self._model_cache: dict[str, Any] = {}

    @property
    def metadata(self) -> dict:
        """Return solver metadata for logging."""
        return {
            "name": self.name,
            "models": self.models,
            "synthesizer": self.synthesizer_model,
            "model_count": len(self.models),
        }

    async def _get_model(self, model_id: str):
        """Get or create an Inspect model instance.

        Uses caching to avoid recreating models.
        """
        if model_id not in self._model_cache:
            from inspect_ai.model import get_model
            self._model_cache[model_id] = get_model(model_id)
        return self._model_cache[model_id]

    async def _query_model(
        self,
        model_id: str,
        state: Any,
        generate: Any
    ) -> str:
        """Query a single model with rate limiting.

        Args:
            model_id: Model identifier
            state: Inspect TaskState
            generate: Inspect generate function

        Returns:
            Model response text
        """
        # Apply rate limiting
        provider = self.rate_limiter.get_provider_from_model(model_id)
        await self.rate_limiter.acquire(provider)

        try:
            # Get the model
            model = await self._get_model(model_id)

            # Generate response
            # Note: We use the model's generate directly for multi-model queries
            messages = state.messages if hasattr(state, 'messages') else []
            response = await model.generate(messages)

            # Extract text from response
            if hasattr(response, 'completion'):
                return response.completion
            elif hasattr(response, 'message') and hasattr(response.message, 'content'):
                return str(response.message.content)
            return str(response)

        except Exception as e:
            # Return error indication rather than failing entirely
            return f"[Error from {model_id}: {str(e)[:200]}]"

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
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Pair responses with model IDs, filtering out exceptions
        response_pairs = []
        for model_id, response in zip(self.models, responses):
            if isinstance(response, Exception):
                response_pairs.append((model_id, f"[Error: {str(response)[:200]}]"))
            else:
                response_pairs.append((model_id, response))

        # Synthesize responses
        return await self._synthesize(state, response_pairs, generate)

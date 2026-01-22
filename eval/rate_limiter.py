"""Rate limiting for multi-model queries.

Implements token bucket algorithm for per-provider rate limiting
to avoid hitting API rate limits during evaluations.
"""

import asyncio
import time
from typing import Optional


class TokenBucketRateLimiter:
    """Token bucket rate limiter for a single provider.

    The bucket starts full and tokens are consumed on each request.
    Tokens refill at a steady rate (RPM/60 per second).
    """

    def __init__(self, rpm: int = 60):
        """Initialize token bucket.

        Args:
            rpm: Requests per minute (max burst capacity)
        """
        self.rpm = rpm
        self.tokens = rpm
        self.last_refill = time.time()
        self._lock = asyncio.Lock()

    def _refill(self):
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_refill

        # Refill at rate of rpm/60 tokens per second
        tokens_to_add = elapsed * (self.rpm / 60.0)
        self.tokens = min(self.rpm, self.tokens + tokens_to_add)
        self.last_refill = now

    async def acquire(self):
        """Acquire a token, waiting if necessary.

        Blocks until a token is available.
        """
        async with self._lock:
            self._refill()

            if self.tokens >= 1:
                self.tokens -= 1
                return

            # Need to wait for a token
            wait_time = (1 - self.tokens) / (self.rpm / 60.0)
            await asyncio.sleep(wait_time)

            self._refill()
            self.tokens -= 1


class RateLimiter:
    """Multi-provider rate limiter.

    Maintains separate token buckets for each provider to allow
    concurrent requests across providers while respecting individual limits.
    """

    # Default rate limits per provider (requests per minute)
    DEFAULT_LIMITS = {
        "anthropic": 60,
        "openai": 60,
        "google": 60,
        "x-ai": 30,  # Grok tends to have lower limits
        "deepseek": 30,
    }

    def __init__(
        self,
        default_rpm: int = 60,
        provider_limits: Optional[dict[str, int]] = None
    ):
        """Initialize rate limiter.

        Args:
            default_rpm: Default RPM for unknown providers
            provider_limits: Custom RPM limits per provider
        """
        self.default_rpm = default_rpm
        self.provider_limits = {**self.DEFAULT_LIMITS}
        if provider_limits:
            self.provider_limits.update(provider_limits)

        self._limiters: dict[str, TokenBucketRateLimiter] = {}
        self._lock = asyncio.Lock()

    def get_limiter(self, provider: str) -> TokenBucketRateLimiter:
        """Get or create a limiter for a provider."""
        if provider not in self._limiters:
            rpm = self.provider_limits.get(provider, self.default_rpm)
            self._limiters[provider] = TokenBucketRateLimiter(rpm)
        return self._limiters[provider]

    async def acquire(self, provider: str):
        """Acquire a token for a specific provider.

        Args:
            provider: Provider name (e.g., "anthropic", "openai")
        """
        limiter = self.get_limiter(provider)
        await limiter.acquire()

    def get_provider_from_model(self, model: str) -> str:
        """Extract provider name from model string.

        Args:
            model: Model string like "anthropic/claude-opus-4-5-20251101"

        Returns:
            Provider name (e.g., "anthropic")
        """
        if "/" in model:
            return model.split("/")[0]
        # Default to anthropic for unqualified names
        return "anthropic"

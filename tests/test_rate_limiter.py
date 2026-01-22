"""Tests for eval/rate_limiter.py - Token bucket rate limiting."""

import asyncio
import pytest
import time


class TestTokenBucketRateLimiter:
    """Tests for TokenBucketRateLimiter class."""

    def test_initialization(self):
        """Token bucket should initialize with correct RPM and full tokens."""
        from eval.rate_limiter import TokenBucketRateLimiter

        limiter = TokenBucketRateLimiter(rpm=60)
        assert limiter.rpm == 60
        assert limiter.tokens == 60

    def test_initialization_custom_rpm(self):
        """Token bucket should accept custom RPM values."""
        from eval.rate_limiter import TokenBucketRateLimiter

        limiter = TokenBucketRateLimiter(rpm=30)
        assert limiter.rpm == 30
        assert limiter.tokens == 30

    @pytest.mark.asyncio
    async def test_acquire_available(self):
        """Acquiring when tokens available should return immediately."""
        from eval.rate_limiter import TokenBucketRateLimiter

        limiter = TokenBucketRateLimiter(rpm=60)
        initial_tokens = limiter.tokens

        start = time.time()
        await limiter.acquire()
        elapsed = time.time() - start

        assert elapsed < 0.1  # Should be nearly instant
        assert limiter.tokens == initial_tokens - 1

    @pytest.mark.asyncio
    async def test_multiple_acquires(self):
        """Multiple acquires should decrement tokens correctly."""
        from eval.rate_limiter import TokenBucketRateLimiter

        limiter = TokenBucketRateLimiter(rpm=10)

        for _ in range(5):
            await limiter.acquire()

        # Allow for small floating point differences due to refill timing
        assert 4.9 < limiter.tokens < 5.1


class TestRateLimiter:
    """Tests for the multi-provider RateLimiter class."""

    def test_per_provider_tracking(self):
        """Each provider should have independent rate limiting."""
        from eval.rate_limiter import RateLimiter

        limiter = RateLimiter(default_rpm=60)

        # Different providers should be tracked separately
        assert limiter.get_limiter("anthropic") is not limiter.get_limiter("openai")

    def test_custom_provider_limits(self):
        """Providers can have custom RPM limits."""
        from eval.rate_limiter import RateLimiter

        limiter = RateLimiter(
            default_rpm=60,
            provider_limits={"anthropic": 30, "openai": 100}
        )

        assert limiter.get_limiter("anthropic").rpm == 30
        assert limiter.get_limiter("openai").rpm == 100
        assert limiter.get_limiter("google").rpm == 60  # Default

    @pytest.mark.asyncio
    async def test_acquire_for_provider(self):
        """Should acquire token for specific provider."""
        from eval.rate_limiter import RateLimiter

        limiter = RateLimiter(default_rpm=60)

        await limiter.acquire("anthropic")
        await limiter.acquire("openai")

        # Each provider should have decremented independently
        assert limiter.get_limiter("anthropic").tokens == 59
        assert limiter.get_limiter("openai").tokens == 59

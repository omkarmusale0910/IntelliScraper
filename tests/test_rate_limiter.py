"""Tests for the RateLimiter token-bucket implementation."""

import asyncio
import time

from intelliscraper.rate_limiter import RateLimiter


class TestRateLimiter:
    """Tests for RateLimiter."""

    def test_disabled_by_default(self):
        """RateLimiter with no arguments should be disabled."""
        limiter = RateLimiter()
        assert not limiter.enabled
        assert limiter.max_rpm == 0

    def test_disabled_with_none(self):
        """RateLimiter with None should be disabled."""
        limiter = RateLimiter(max_requests_per_minute=None)
        assert not limiter.enabled

    def test_disabled_with_zero(self):
        """RateLimiter with 0 should be disabled."""
        limiter = RateLimiter(max_requests_per_minute=0)
        assert not limiter.enabled

    def test_enabled_with_positive_value(self):
        """RateLimiter with a positive value should be enabled."""
        limiter = RateLimiter(max_requests_per_minute=60)
        assert limiter.enabled
        assert limiter.max_rpm == 60

    def test_acquire_no_limit_returns_immediately(self):
        """acquire() should return immediately when disabled."""

        async def _run():
            limiter = RateLimiter()
            start = time.monotonic()
            await limiter.acquire()
            elapsed = time.monotonic() - start
            assert elapsed < 0.05  # Should be nearly instant

        asyncio.run(_run())

    def test_acquire_respects_rate_limit(self):
        """Two rapid acquire() calls should be spaced by the interval."""

        async def _run():
            # 600 RPM = 10/sec = 0.1s interval
            limiter = RateLimiter(max_requests_per_minute=600)

            await limiter.acquire()  # First call — immediate
            start = time.monotonic()
            await limiter.acquire()  # Second call — should wait ~0.1s
            elapsed = time.monotonic() - start

            assert elapsed >= 0.08  # Allow small timing tolerance

        asyncio.run(_run())

    def test_acquire_shared_across_tasks(self):
        """Multiple concurrent tasks should share the rate limit."""

        async def _run():
            # 300 RPM = 5/sec = 0.2s interval
            limiter = RateLimiter(max_requests_per_minute=300)

            results = []

            async def worker(worker_id: int):
                await limiter.acquire()
                results.append((worker_id, time.monotonic()))

            start = time.monotonic()
            await asyncio.gather(worker(1), worker(2), worker(3))
            total_elapsed = time.monotonic() - start

            # 3 requests at 0.2s interval = ~0.4s minimum
            assert total_elapsed >= 0.35
            assert len(results) == 3

        asyncio.run(_run())

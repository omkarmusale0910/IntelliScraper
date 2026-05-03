"""Token-bucket rate limiter for controlling request throughput.

Enforces a global request rate across all concurrent browser pages.
When multiple pages share a single ``RateLimiter``, the combined
throughput of all pages is capped at the configured limit.

Example::

    # 15 requests per second = 900 per minute
    limiter = RateLimiter(max_requests_per_minute=900)

    # Before each request (called from multiple concurrent pages):
    await limiter.acquire()   # blocks until a token is available
    await page.goto(url)

    # Disable rate limiting (default):
    limiter = RateLimiter()   # or RateLimiter(max_requests_per_minute=None)
"""

from __future__ import annotations

import asyncio
import logging
import time

logger = logging.getLogger(__name__)


class RateLimiter:
    """Token-bucket rate limiter shared across all concurrent pages.

    The rate limit is enforced **globally** — if you have 4 concurrent
    pages and a limit of 900 requests/minute (15/sec), all 4 pages
    share that 15/sec budget, not 15/sec each.

    Args:
        max_requests_per_minute: Maximum requests allowed per minute.
            Set to ``None`` or ``0`` to disable rate limiting (default).

    Attributes:
        enabled: Whether rate limiting is active.
        max_rpm: The configured maximum requests per minute.

    Example::

        # No rate limiting (default)
        limiter = RateLimiter()

        # 15 requests per second across all pages
        limiter = RateLimiter(max_requests_per_minute=900)

        # Conservative limit for protected sites
        limiter = RateLimiter(max_requests_per_minute=60)  # 1/sec
    """

    def __init__(
        self,
        max_requests_per_minute: int | None = None,
    ) -> None:
        self._max_rpm = max_requests_per_minute or 0
        self._enabled = self._max_rpm > 0
        self._lock = asyncio.Lock()

        if self._enabled:
            self._min_interval = 60.0 / self._max_rpm
            self._last_request_time = 0.0
            logger.info(
                "Rate limiter enabled: %d requests/minute " "(%.2f sec interval)",
                self._max_rpm,
                self._min_interval,
            )
        else:
            self._min_interval = 0.0
            self._last_request_time = 0.0
            logger.debug("Rate limiter disabled (no limit)")

    @property
    def enabled(self) -> bool:
        """Whether rate limiting is active."""
        return self._enabled

    @property
    def max_rpm(self) -> int:
        """The configured maximum requests per minute."""
        return self._max_rpm

    async def acquire(self) -> None:
        """Wait until a request token is available.

        If rate limiting is disabled, returns immediately.  Otherwise,
        blocks until enough time has elapsed since the last request to
        stay within the configured rate.

        This method is safe to call from multiple concurrent tasks —
        an ``asyncio.Lock`` ensures only one task checks and updates
        the timestamp at a time.
        """
        if not self._enabled:
            return

        async with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_request_time
            wait_time = self._min_interval - elapsed

            if wait_time > 0:
                logger.debug(
                    "Rate limiter: waiting %.2fs before next request "
                    "(%.0f rpm limit)",
                    wait_time,
                    self._max_rpm,
                )
                await asyncio.sleep(wait_time)

            self._last_request_time = time.monotonic()

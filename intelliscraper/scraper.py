"""Async web scraper with rate limiting and concurrent page support.

The ``AsyncScraper`` class is the main entry point for IntelliScraper.
It orchestrates browser backends, rate limiting, and page management
to scrape one or many URLs concurrently.

Two browser modes are supported:

- **Local browser** (``use_local_browser=True``): Connects to your
  running Chrome instance via CDP.  All existing cookies and logins
  are available immediately.
- **Managed browser** (default): Launches a fresh Chromium instance
  with fingerprint spoofing, proxy, and session data.

Example::

    import asyncio
    from intelliscraper import AsyncScraper, ScrapStatus

    async def main():
        async with AsyncScraper(max_concurrent_pages=4) as scraper:
            response = await scraper.scrape("https://example.com")
            if response.status == ScrapStatus.SUCCESS:
                print(response.scrap_html_content)

    asyncio.run(main())
"""

from __future__ import annotations

import asyncio
import copy
import logging
import random
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING

from playwright.async_api import Page
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from playwright.async_api import async_playwright

from intelliscraper.browser.local import LocalBrowserBackend
from intelliscraper.browser.managed import ManagedBrowserBackend
from intelliscraper.common.constants import (
    BROWSER_LAUNCH_OPTIONS,
    MAX_PAUSE_MS,
    MAX_SCROLL_WAIT_MS,
    MIN_PAUSE_MS,
    MIN_SCROLL_WAIT_MS,
)
from intelliscraper.common.models import (
    Proxy,
    RequestEvent,
    ScrapeRequest,
    ScrapeResponse,
    Session,
)
from intelliscraper.enums import BrowsingMode, ScrapStatus
from intelliscraper.proxy.base import ProxyProvider
from intelliscraper.rate_limiter import RateLimiter

if TYPE_CHECKING:
    from intelliscraper.browser.backend import BrowserBackend

logger = logging.getLogger(__name__)


class AsyncScraper:
    """Async web scraper with rate limiting and concurrent page support.

    Orchestrates browser backends, page pools, rate limiting, and
    human-like browsing behaviour to scrape URLs concurrently.

    Args:
        headless: Run browser without UI.  Only applies in managed
            browser mode.  Ignored when ``use_local_browser=True``.
            Defaults to ``True``.
        browser_launch_options: Custom Chromium launch options.  Only
            applies in managed browser mode.  Defaults to
            ``BROWSER_LAUNCH_OPTIONS``.
        proxy: Proxy configuration or ``ProxyProvider`` instance.
            Only applies in managed browser mode.  Defaults to
            ``None``.
        session_data: Pre-authenticated session with cookies,
            localStorage, sessionStorage, and browser fingerprint.
            Only applies in managed browser mode.  Defaults to
            ``None``.
        browsing_mode: Behaviour mode — ``FAST`` (no human
            simulation) or ``HUMAN_LIKE`` (scrolling, delays).
            Auto-determined if ``None``.  Defaults to ``None``.
        max_concurrent_pages: Number of pages to use for concurrent
            scraping.  Defaults to ``1``.
        use_local_browser: If ``True``, connect to an existing Chrome
            instance via CDP instead of launching a new browser.
            Defaults to ``False``.
        max_requests_per_minute: Rate limit shared across all pages.
            Set to ``None`` or ``0`` to disable (default).

    Note:
        ``__init__`` only sets configuration.  Call ``initialize()``
        or use the async context manager to start the browser::

            async with AsyncScraper() as scraper:
                result = await scraper.scrape(url)
    """

    def __init__(
        self,
        headless: bool = True,
        browser_launch_options: dict = BROWSER_LAUNCH_OPTIONS,
        proxy: Proxy | ProxyProvider | None = None,
        session_data: Session | None = None,
        browsing_mode: BrowsingMode | None = None,
        max_concurrent_pages: int = 1,
        use_local_browser: bool = False,
        max_requests_per_minute: int | None = None,
    ) -> None:
        logger.debug("Initializing AsyncScraper")

        self.use_local_browser = use_local_browser
        self.headless = headless
        self.browser_launch_options = copy.deepcopy(browser_launch_options)
        self.browser_launch_options.update({"headless": headless})

        # Resolve proxy.
        if proxy is not None and isinstance(proxy, ProxyProvider):
            logger.debug(
                "Converting ProxyProvider to Proxy: %s",
                proxy.__class__.__name__,
            )
            self.proxy = proxy.get_proxy()
        else:
            self.proxy = proxy

        self.session_data = session_data
        self.max_concurrent_pages = max_concurrent_pages
        self._closed = False
        self._initialized = False

        self._playwright = None
        self._browser = None
        self._context = None
        self._page_pool: list[Page] = []
        self._semaphore: asyncio.Semaphore | None = None

        # Rate limiter (shared across all pages).
        self._rate_limiter = RateLimiter(
            max_requests_per_minute=max_requests_per_minute
        )

        # Determine browsing mode.
        self.browsing_mode = self._resolve_browsing_mode(browsing_mode)

        # Create the backend.
        self._backend: BrowserBackend = self._create_backend()

        # Determine browser mode label for responses.
        self._browser_mode_label = (
            "local_browser" if use_local_browser else "managed_browser"
        )

        if self.proxy:
            logger.info("Using proxy: %s", self.proxy.server)
        if session_data:
            logger.info("Using session data for authenticated scraping")
        logger.info(
            "Scraper mode: %s | pages: %d | browsing: %s | " "rate limit: %s rpm",
            self._browser_mode_label,
            self.max_concurrent_pages,
            self.browsing_mode.value,
            self._rate_limiter.max_rpm or "unlimited",
        )

    # ── Initialisation ────────────────────────────────────────────────

    async def initialize(self) -> None:
        """Initialise browser and create the page pool.

        Dispatches to the configured backend to start the browser,
        then creates ``max_concurrent_pages`` pages and a semaphore.
        """
        if self._initialized:
            return

        logger.debug("Starting async initialisation")
        self._playwright = await async_playwright().start()

        self._browser, self._context = await self._backend.initialize(self._playwright)

        logger.debug(
            "Creating page pool with %d pages",
            self.max_concurrent_pages,
        )
        for i in range(self.max_concurrent_pages):
            page = await self._create_configured_page()
            self._page_pool.append(page)
            logger.debug("Created page %d/%d", i + 1, self.max_concurrent_pages)

        self._semaphore = asyncio.Semaphore(self.max_concurrent_pages)
        self._initialized = True
        logger.info(
            "AsyncScraper initialised | mode: %s | pages: %d",
            self._browser_mode_label,
            self.max_concurrent_pages,
        )

    # ── Context managers ──────────────────────────────────────────────

    async def __aenter__(self) -> AsyncScraper:
        """Async context manager entry — initialises the scraper."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> bool:
        """Async context manager exit — closes the scraper."""
        await self.close()
        return False

    async def close(self) -> None:
        """Close browser and release all resources.

        Behaviour depends on the backend:

        - **Local browser**: Only closes pages opened by the scraper.
          The Chrome process and context are left running.
        - **Managed browser**: Closes pages, context, and browser.
        """
        if self._closed:
            return

        self._closed = True
        logger.debug("Starting async cleanup ...")

        try:
            for page in self._page_pool:
                try:
                    await page.close()
                except Exception as exc:
                    logger.debug("Failed to close page: %s", exc)

            await self._backend.cleanup(self._browser, self._context)

            if self._playwright:
                await self._playwright.stop()

            logger.debug("Async cleanup complete")
        except Exception as exc:
            logger.error("Error during async cleanup: %s", exc)

    def __del__(self) -> None:
        """Destructor — warns if the scraper was not properly closed."""
        if not self._closed and self._initialized:
            logger.warning(
                "AsyncScraper was not properly closed.  "
                "Use 'async with AsyncScraper()' or call "
                "'await scraper.close()'"
            )

    # ── Public API ────────────────────────────────────────────────────

    async def scrape(
        self,
        url: str,
        timeout: timedelta = timedelta(seconds=30),
    ) -> ScrapeResponse:
        """Scrape content from a single URL.

        The semaphore ensures only ``max_concurrent_pages`` requests
        run simultaneously.  Pages are selected from the pool using
        round-robin.  Rate limiting is applied before navigation.

        Args:
            url: Target URL to scrape.
            timeout: Maximum time to wait for page load.  Defaults
                to 30 seconds.

        Returns:
            A ``ScrapeResponse`` with status, HTML content, HTTP
            status code, timing, and metadata.

        Example::

            async with AsyncScraper(max_concurrent_pages=4) as scraper:
                tasks = [
                    scraper.scrape("https://example1.com"),
                    scraper.scrape("https://example2.com"),
                ]
                results = await asyncio.gather(*tasks)
        """
        sent_at = datetime.now(timezone.utc).timestamp()

        async with self._semaphore:
            page = self._get_available_page()
            try:
                scrape_request = ScrapeRequest(
                    url=url,
                    timeout=timeout,
                    browser_launch_options=self.browser_launch_options,
                    proxy=self.proxy,
                    session_data=self.session_data,
                    browsing_mode=self.browsing_mode,
                )

                if self._closed:
                    logger.error("Cannot scrape: scraper is closed")
                    raise RuntimeError(
                        "Scraper is closed.  Create a new instance "
                        "or use the context manager."
                    )

                if self.session_data and not url.startswith(self.session_data.base_url):
                    logger.warning(
                        "URL %s does not match session base URL %s.  "
                        "Scraping may fail due to invalid session.",
                        url,
                        self.session_data.base_url,
                    )

                self._validate_url(url)
                logger.info("Scraping: %s", url)

                # Apply rate limiting before navigation.
                await self._rate_limiter.acquire()

                logger.debug("Navigating to: %s", url)
                response = await page.goto(
                    url=url,
                    wait_until="networkidle",
                    timeout=timeout.total_seconds() * 1000,
                )

                # Capture HTTP status code from the server response.
                http_status_code = response.status if response else None
                logger.debug("Page loaded: %s (HTTP %s)", url, http_status_code)

                # Check for rate limiting or blocking.
                status = self._classify_http_status(http_status_code)

                if self.browsing_mode == BrowsingMode.HUMAN_LIKE:
                    await self._apply_human_like_behavior(page)

                html_content = await page.content()
                elapsed_time = datetime.now(timezone.utc).timestamp() - sent_at

                logger.info(
                    "Scraping finished: %s in %.2fs " "(HTTP %s, status=%s)",
                    url,
                    elapsed_time,
                    http_status_code,
                    status.value,
                )
                self._record_event(sent_at=sent_at, status=status)
                return ScrapeResponse(
                    scrape_request=scrape_request,
                    status=status,
                    http_status_code=http_status_code,
                    elapsed_time=elapsed_time,
                    scrap_html_content=html_content,
                    session_id=self._get_session_id(),
                    browser_mode=self._browser_mode_label,
                )

            except PlaywrightTimeoutError as exc:
                html_content = await page.content()
                elapsed_time = datetime.now(timezone.utc).timestamp() - sent_at

                # If we captured meaningful HTML before the timeout, it's a partial success
                if html_content and len(html_content.strip()) > 100:
                    status = ScrapStatus.PARTIAL_SUCCESS
                else:
                    status = ScrapStatus.TIMEOUT

                self._record_event(sent_at=sent_at, status=status)
                logger.warning(
                    "Timeout scraping %s after %.1fs.  "
                    "Returning partial content (status=%s).",
                    url,
                    timeout.total_seconds(),
                    status.value,
                )
                return ScrapeResponse(
                    scrape_request=scrape_request,
                    status=status,
                    elapsed_time=elapsed_time,
                    scrap_html_content=html_content,
                    error_msg=str(exc),
                    session_id=self._get_session_id(),
                    browser_mode=self._browser_mode_label,
                )

            except Exception as exc:
                elapsed_time = datetime.now(timezone.utc).timestamp() - sent_at
                logger.error("Failed to scrape %s: %s", url, exc, exc_info=True)
                self._record_event(sent_at=sent_at, status=ScrapStatus.FAILED)
                return ScrapeResponse(
                    scrape_request=scrape_request,
                    status=ScrapStatus.FAILED,
                    elapsed_time=elapsed_time,
                    error_msg=str(exc),
                    session_id=self._get_session_id(),
                    browser_mode=self._browser_mode_label,
                )

    async def batch_scrape(
        self,
        urls: list[str],
        timeout: timedelta = timedelta(seconds=30),
    ) -> list[ScrapeResponse]:
        """Scrape multiple URLs with rate limiting and concurrency control.

        This is the recommended API for scraping large numbers of URLs.
        Rate limiting (via ``max_requests_per_minute``) is applied
        before each request, and the page-pool semaphore controls
        concurrency.

        Args:
            urls: List of target URLs to scrape.
            timeout: Maximum time per page load.  Defaults to
                30 seconds.

        Returns:
            List of ``ScrapeResponse`` objects, one per URL, in the
            same order as the input URLs.

        Example::

            async with AsyncScraper(
                max_concurrent_pages=4,
                max_requests_per_minute=900,  # 15/sec
            ) as scraper:
                results = await scraper.batch_scrape(
                    urls=[f"https://example.com/page/{i}" for i in range(100)]
                )
                for result in results:
                    print(result.scrape_request.url, result.status)
        """
        logger.info(
            "Starting batch scrape of %d URLs " "(concurrency=%d, rate_limit=%s rpm)",
            len(urls),
            self.max_concurrent_pages,
            self._rate_limiter.max_rpm or "unlimited",
        )

        tasks = [self.scrape(url=url, timeout=timeout) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=False)

        # Summarise results.
        status_counts = {}
        for result in results:
            status_value = result.status.value
            status_counts[status_value] = status_counts.get(status_value, 0) + 1

        logger.info(
            "Batch scrape complete: %d URLs — %s",
            len(urls),
            ", ".join(f"{k}: {v}" for k, v in sorted(status_counts.items())),
        )

        return list(results)

    # ── Private helpers ───────────────────────────────────────────────

    def _resolve_browsing_mode(
        self,
        explicit_mode: BrowsingMode | None,
    ) -> BrowsingMode:
        """Determine the browsing mode based on configuration.

        Priority:
        1. Explicit ``browsing_mode`` always wins.
        2. Local browser → ``HUMAN_LIKE`` (real Chrome, act human).
        3. Proxy provided → ``FAST`` (proxy handles identity).
        4. Session data → ``HUMAN_LIKE`` (authenticated, be subtle).
        5. Default → ``HUMAN_LIKE``.

        Args:
            explicit_mode: Explicitly requested mode, or ``None``.

        Returns:
            The resolved ``BrowsingMode``.
        """
        if explicit_mode:
            return explicit_mode
        if self.use_local_browser:
            return BrowsingMode.HUMAN_LIKE
        if self.proxy:
            return BrowsingMode.FAST
        return BrowsingMode.HUMAN_LIKE

    def _create_backend(self) -> BrowserBackend:
        """Create the appropriate browser backend.

        Returns:
            A ``LocalBrowserBackend`` or ``ManagedBrowserBackend``
            based on the ``use_local_browser`` flag.
        """
        if self.use_local_browser:
            return LocalBrowserBackend(headless=self.headless)
        return ManagedBrowserBackend(
            headless=self.headless,
            browser_launch_options=self.browser_launch_options,
            proxy=self.proxy,
            session_data=self.session_data,
        )

    async def _create_configured_page(self) -> Page:
        """Create a new page with session storage applied.

        Returns:
            A configured Playwright ``Page`` instance.
        """
        logger.debug("Creating and configuring new page")
        page = await self._context.new_page()

        # Apply session storage if using managed backend.
        if isinstance(self._backend, ManagedBrowserBackend):
            await self._backend.apply_session_storage(page)

        return page

    def _get_available_page(self) -> Page:
        """Get the next available page from the pool (round-robin).

        Returns:
            A ``Page`` from the pool.
        """
        page = self._page_pool.pop(0)
        self._page_pool.append(page)
        return page

    def _validate_url(self, url: str) -> None:
        """Validate that the URL has a proper HTTP(S) scheme.

        Args:
            url: URL string to validate.

        Raises:
            ValueError: If the URL is empty or doesn't start with
                ``http://`` or ``https://``.
        """
        if not url or not url.startswith(("http://", "https://")):
            raise ValueError(f"Invalid URL: {url}")

    def _classify_http_status(self, http_status_code: int | None) -> ScrapStatus:
        """Map an HTTP status code to a ``ScrapStatus``.

        Args:
            http_status_code: The HTTP status code, or ``None``.

        Returns:
            The appropriate ``ScrapStatus``.
        """
        if http_status_code is None:
            return ScrapStatus.SUCCESS

        if http_status_code is None:
            return ScrapStatus.FAILED

        if http_status_code == 429:
            return ScrapStatus.RATE_LIMITED
        if http_status_code == 403:
            return ScrapStatus.BLOCKED
        if 200 <= http_status_code < 400:
            return ScrapStatus.SUCCESS

        if http_status_code is None:
            return ScrapStatus.FAILED

        return ScrapStatus.SUCCESS

    def _get_session_id(self) -> str | None:
        """Return the session site identifier, or ``None``.

        Returns:
            The ``site`` field from the configured session data.
        """
        return self.session_data.site if self.session_data else None

    def _record_event(self, status: ScrapStatus, sent_at: float) -> None:
        """Record a scraping event to the session statistics.

        If session data is configured, adds a ``RequestEvent`` to the
        session's time-series log for performance analysis.

        Args:
            status: Outcome status of the request.
            sent_at: Unix timestamp when the request was sent.
        """
        if self.session_data:
            self.session_data.stats.add_request_event(
                request_event=RequestEvent(sent_at=sent_at, request_status=status)
            )

    async def _apply_human_like_behavior(self, page: Page) -> None:
        """Apply human-like scrolling behaviour to avoid bot detection.

        Performs a smooth scroll to a random position with realistic
        timing delays.

        Args:
            page: Playwright ``Page`` to apply behaviour to.
        """
        try:
            page_height = await page.evaluate("document.body.scrollHeight")
            if page_height <= 0:
                return

            scroll_pos = int(page_height * random.uniform(0.2, 0.8))
            await page.evaluate(
                f"""
                window.scrollTo({{
                    top: {scroll_pos},
                    behavior: 'smooth'
                }});
            """
            )
            await page.wait_for_timeout(
                random.randint(MIN_SCROLL_WAIT_MS, MAX_SCROLL_WAIT_MS)
            )
            await page.wait_for_timeout(random.randint(MIN_PAUSE_MS, MAX_PAUSE_MS))
        except Exception as exc:
            logger.debug("Human-like behaviour failed: %s", exc)

import asyncio
import copy
import json
import logging
import random
from datetime import datetime, timedelta, timezone

from playwright.async_api import Page
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from playwright.async_api import async_playwright

from intelliscraper.common.constants import (
    BROWSER_LAUNCH_OPTIONS,
    DEFAULT_BROWSER_FINGERPRINT,
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


class AsyncScraper:
    """An async web scraper that retrieves HTML content from URLs concurrently."""

    def __init__(
        self,
        headless: bool = True,
        browser_launch_options: dict = BROWSER_LAUNCH_OPTIONS,
        proxy: Proxy | ProxyProvider | None = None,
        session_data: Session | None = None,
        browsing_mode: BrowsingMode | None = None,
        max_concurrent_pages: int = 4,
    ):
        """Initialize the async scraper with browser and session configuration.

        Args:
            headless: Run browser without UI. Defaults to True.
            browser_launch_options: Custom Chromium launch options. If None, uses
                default options. Defaults to None.
            proxy: Proxy configuration or ProxyProvider instance. Defaults to None.
            session_data: Pre-authenticated session with cookies, localStorage,
                sessionStorage, and browser fingerprint. Defaults to None.
            browsing_mode: Behavior mode - FAST (no human simulation) or HUMAN_LIKE
                (scrolling, delays). Auto-determined if None. Defaults to None.
            max_concurrent_pages: Number of pages to use for concurrent scraping.
                Defaults to 4.

        Note:
            This __init__ only sets configuration. Call initialize() or use
            async context manager to actually start the browser.
        """
        logging.debug("Initializing AsyncScraper")
        self.headless = headless
        self.browser_launch_options = copy.deepcopy(browser_launch_options)
        self.browser_launch_options.update({"headless": headless})

        if proxy is not None and isinstance(proxy, ProxyProvider):
            logging.debug(
                f"Converting ProxyProvider to Proxy: {proxy.__class__.__name__}"
            )
            self.proxy = proxy.get_proxy()
        else:
            self.proxy = proxy

        self.session_data = session_data
        self.max_concurrent_pages = max_concurrent_pages
        self._closed = False
        self._initialized = False

        self.playwright = None
        self.browser = None
        self.context = None
        self.page_pool = []
        self.semaphore = None

        # Determine browsing mode based on priority
        # Priority logic:
        # - If a proxy is provided, it takes priority (use proxy).
        # - If no proxy but session data is provided, load session cookies and metadata into the context.
        # - If neither proxy nor session data is provided, start a fresh context.
        if browsing_mode:
            self.browsing_mode = browsing_mode
        elif self.proxy:
            self.browsing_mode = BrowsingMode.FAST
        elif self.session_data:
            self.browsing_mode = BrowsingMode.HUMAN_LIKE
        else:
            self.browsing_mode = BrowsingMode.HUMAN_LIKE

        if self.proxy:
            logging.info(f"Using proxy: {self.proxy.server}")
        if session_data:
            logging.info("Using session data for authenticated scraping")
        logging.info(f"Scraper will use {self.max_concurrent_pages} concurrent pages")

    async def initialize(self):
        """Initialize browser and create page pool.

        This method starts playwright, launches browser, and creates the page pool.
        """
        if self._initialized:
            return

        logging.debug("Starting async initialization")

        self.playwright = await async_playwright().start()

        logging.debug(f"Launching browser with options: {self.browser_launch_options}")
        self.browser = await self.playwright.chromium.launch(
            **self.browser_launch_options
        )
        logging.debug("Browser launched successfully")

        # Create browser context with fingerprint
        browser_fingerprint = (
            self.session_data.fingerprint
            if self.session_data
            else DEFAULT_BROWSER_FINGERPRINT
        )

        await self._create_browser_context(
            browser_fingerprint=browser_fingerprint, proxy=self.proxy
        )

        await self._add_cookies()

        # Apply anti-detection
        self._apply_anti_detection_scripts()

        logging.debug(f"Creating page pool with {self.max_concurrent_pages} pages")
        for i in range(self.max_concurrent_pages):
            page = await self._create_configured_page()
            self.page_pool.append(page)
            logging.debug(f"Created page {i+1}/{self.max_concurrent_pages}")

        # Semaphore to limit concurrent requests
        self.semaphore = asyncio.Semaphore(self.max_concurrent_pages)

        self._initialized = True
        logging.info(f"AsyncScraper initialized with {self.max_concurrent_pages} pages")

    async def __aenter__(self):
        """Async context manager entry point."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit point."""
        await self.close()
        return False

    async def close(self):
        """Close browser and cleanup all resources."""
        if self._closed:
            return

        self._closed = True
        logging.debug("Starting async cleanup...")

        try:
            # Close all pages in pool
            for page in self.page_pool:
                try:
                    await page.close()
                except Exception as e:
                    logging.debug(f"Failed to close page: {e}")

            # Close context
            if self.context:
                await self.context.close()

            # Close browser
            if self.browser:
                await self.browser.close()

            # Stop playwright
            if self.playwright:
                await self.playwright.stop()

            logging.debug("Async cleanup complete")

        except Exception as e:
            logging.error(f"Error during async cleanup: {e}")

    def __del__(self):
        """Destructor for fallback cleanup."""
        if not self._closed and self._initialized:
            logging.warning(
                "AsyncScraper was not properly closed. "
                "Use 'async with AsyncScraper()' or call 'await scraper.close()'"
            )

    async def _create_browser_context(
        self, browser_fingerprint: dict | None, proxy: Proxy | None
    ):
        """Create browser context with fingerprint and proxy.

        Args:
            browser_fingerprint: Browser fingerprint for anti-detection.
            proxy: Proxy configuration.
        """
        logging.debug("Creating browser context")
        if browser_fingerprint is None:
            browser_fingerprint = DEFAULT_BROWSER_FINGERPRINT

        if proxy:
            proxy = proxy.model_dump()

        screen = browser_fingerprint.get("screenResolution", {})

        self.context = await self.browser.new_context(
            viewport={
                "width": screen.get("width", 1920),
                "height": screen.get("height", 1080),
            },
            screen={
                "width": screen.get("width", 1920),
                "height": screen.get("height", 1080),
            },
            proxy=proxy,
            geolocation={
                "latitude": random.uniform(-90, 90),
                "longitude": random.uniform(-180, 180),
            },
            user_agent=browser_fingerprint.get(
                "userAgent", "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
            ),
            locale=browser_fingerprint.get("language", "en-US"),
            timezone_id=browser_fingerprint.get("timezone", "Asia/Calcutta"),
            device_scale_factor=1,
            is_mobile=False,
            has_touch=False,
            color_scheme="light",
            ignore_https_errors=True,
            extra_http_headers={
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Accept-Language": f"{browser_fingerprint.get('language', 'en-US')},en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "DNT": "1",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            },
        )
        logging.debug("Browser context created successfully")

    async def _add_cookies(self):
        """Add cookies from session data to the browser context."""
        if self.session_data and self.session_data.cookies:
            logging.debug(f"Adding {len(self.session_data.cookies)} cookies")
            await self.context.add_cookies(self.session_data.cookies)
            logging.debug("Cookies added successfully")

    def _apply_anti_detection_scripts(self):
        """Apply JavaScript scripts to mask automation and avoid bot detection."""
        logging.debug("Applying anti-detection scripts")
        browser_fingerprint = (
            self.session_data.fingerprint
            if self.session_data
            else DEFAULT_BROWSER_FINGERPRINT
        )
        self.context.add_init_script(
            f"""
            // Remove webdriver flag (MOST IMPORTANT!)
            Object.defineProperty(navigator, 'webdriver', {{
                get: () => undefined
            }});
            
            // Add chrome object
            window.chrome = {{
                runtime: {{}}
            }};
            
            // Override permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({{ state: Notification.permission }}) :
                    originalQuery(parameters)
            );
            
            // Spoof plugins
            Object.defineProperty(navigator, 'plugins', {{
                get: () => [
                    {{
                        0: {{type: "application/x-google-chrome-pdf", suffixes: "pdf"}},
                        description: "Portable Document Format",
                        filename: "internal-pdf-viewer",
                        length: 1,
                        name: "Chrome PDF Plugin"
                    }},
                    {{
                        0: {{type: "application/pdf", suffixes: "pdf"}},
                        description: "Portable Document Format",
                        filename: "mhjfbmdgcfjbbpaeojofohoefgiehjai",
                        length: 1,
                        name: "Chrome PDF Viewer"
                    }}
                ]
            }});
            
            // Languages
            Object.defineProperty(navigator, 'languages', {{
                get: () => {json.dumps(browser_fingerprint.get('languages', ['en-US']))}
            }});
            
            // Hardware (from fingerprint)
            Object.defineProperty(navigator, 'hardwareConcurrency', {{
                get: () => {browser_fingerprint.get('hardwareConcurrency', 8)}
            }});
            
            Object.defineProperty(navigator, 'deviceMemory', {{
                get: () => {browser_fingerprint.get('deviceMemory', 8)}
            }});
            
            Object.defineProperty(navigator, 'platform', {{
                get: () => "{browser_fingerprint.get('platform', 'Linux x86_64')}"
            }});
            
            // Screen properties
            Object.defineProperty(screen, 'colorDepth', {{
                get: () => {browser_fingerprint.get("screenResolution", {}).get('colorDepth', 24)}
            }});
            
            Object.defineProperty(screen, 'pixelDepth', {{
                get: () => {browser_fingerprint.get("screenResolution", {}).get('colorDepth', 24)}
            }});
            
            // WebGL (from fingerprint)
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {{
                if (parameter === 37445) {{
                    return "{browser_fingerprint.get('webglVendor', 'Google Inc. (Intel)')}";
                }}
                if (parameter === 37446) {{
                    return "{browser_fingerprint.get('webglRenderer', 'ANGLE (Intel)')}";
                }}
                return getParameter.call(this, parameter);
            }};
        """
        )
        logging.debug("Anti-detection scripts applied")

    async def _create_configured_page(self) -> Page:
        """Create a new page with session storage applied.

        Creates and configures a page once during initialization.

        Returns:
            Page: A configured Playwright page instance.
        """
        logging.debug("Creating and configuring new page")
        page = await self.context.new_page()

        # Apply session storage if available
        if self.session_data and (
            self.session_data.localStorage or self.session_data.sessionStorage
        ):
            logging.debug("Applying session | local storage")
            await page.goto(self.session_data.base_url)

            if self.session_data.localStorage:
                await page.evaluate(
                    """
                    (items) => {
                        for (let key in items) {
                            try {
                                localStorage.setItem(key, items[key]);
                            } catch(e) {
                                console.error('Failed to set localStorage:', key, e);
                            }
                        }
                    }
                    """,
                    self.session_data.localStorage,
                )

            if self.session_data.sessionStorage:
                await page.evaluate(
                    """
                    (items) => {
                        for (let key in items) {
                            try {
                                sessionStorage.setItem(key, items[key]);
                            } catch(e) {
                                console.error('Failed to set sessionStorage:', key, e);
                            }
                        }
                    }
                    """,
                    self.session_data.sessionStorage,
                )
            logging.debug("Session storage applied successfully")

        return page

    def _get_available_page(self) -> Page:
        """Get next available page from pool using round-robin.

        Uses round-robin to distribute requests across pages.

        Returns:
            Page: A page from the pool.
        """
        page = self.page_pool.pop(0)
        self.page_pool.append(page)
        return page

    def _validate_url(self, url: str):
        """Validate that the URL has a proper format."""
        if not url or not url.startswith(("http://", "https://")):
            raise ValueError(f"Invalid URL: {url}")

    def _record_event(self, status: ScrapStatus, sent_at: float):
        """Record a scraping event to the session statistics.

        If session data is configured, this method adds a new request event to the
        session's time-series statistics log. The event includes the timestamp and
        the outcome status of the scraping attempt.

        Use Cases:
            The recorded event data is valuable for:

            - **Rate Limiting Analysis**: Identify if too many requests are causing failures.
            By analyzing the time-series data, you can detect patterns like:
            - Sudden spike in failures after rapid requests
            - Consistent failures during specific time windows
            - Success rate degradation over time

        Note:
            If no session_data is configured for this scraper instance, this method
            does nothing (no-op). Events are only recorded when session tracking is enabled.

        Thread-safety:
            This method is thread-safe when session_data.stats uses proper locking
            (which it does via the internal Lock in SessionStats).
        """
        if self.session_data:
            self.session_data.stats.add_request_event(
                request_event=RequestEvent(sent_at=sent_at, request_status=status)
            )

    async def _apply_human_like_behavior(self, page: Page) -> None:
        """
        Apply human-like scrolling behavior to avoid bot detection.

        Performs a smooth scroll to a random position on the page with
        realistic timing delays.

        Args:
            page: Playwright Page instance to apply behavior to

        """
        try:
            # Get page height
            page_height = await page.evaluate("document.body.scrollHeight")

            if page_height <= 0:
                return

            # Random scroll position (20% to 80% of page)
            scroll_pos = int(page_height * random.uniform(0.2, 0.8))

            await page.evaluate(
                f"""
                window.scrollTo({{
                    top: {scroll_pos},
                    behavior: 'smooth'
                }});
            """
            )

            # Wait for scroll animation
            await page.wait_for_timeout(
                random.randint(MIN_SCROLL_WAIT_MS, MAX_SCROLL_WAIT_MS)
            )

            # Additional pause
            await page.wait_for_timeout(random.randint(MIN_PAUSE_MS, MAX_PAUSE_MS))

        except Exception as e:
            logging.debug(f"Human-like behavior failed: {e}")

    async def scrape(
        self,
        url: str,
        timeout: timedelta = timedelta(seconds=30),
    ) -> ScrapeResponse:
        """Scrape content from a URL asynchronously.


        The semaphore ensures only max_concurrent_pages requests run simultaneously.
        Pages are selected from the pool using round-robin.

        Args:
            url: Target URL to scrape.
            timeout: Maximum time to wait for page load. Defaults to 30 seconds.

        Returns:
            ScrapeResponse: Response object containing status, HTML, and metadata.

        Examples:
            Scrape 4 URLs concurrently:
            >>> async with AsyncScraper(max_concurrent_pages=4) as scraper:
            ...     tasks = [
            ...         scraper.scrape("https://example1.com"),
            ...         scraper.scrape("https://example2.com"),
            ...         scraper.scrape("https://example3.com"),
            ...         scraper.scrape("https://example4.com"),
            ...     ]
            ...     results = await asyncio.gather(*tasks)

            Scrape 100 URLs with batching:
            >>> urls = [f"https://example.com/page{i}" for i in range(100)]
            >>> async with AsyncScraper(max_concurrent_pages=4) as scraper:
            ...     results = await asyncio.gather(*[scraper.scrape(url) for url in urls])

        Note:
            - Returns PARTIAL status if timeout occurs (with partial content)
            - Returns FAILED status if other errors occur
            - Applies scrolling and delays in HUMAN_LIKE mode
            - For advanced behavior (mouse movements, clicks), extend this class
        """
        sent_at = datetime.now(timezone.utc).timestamp()

        # Only max_concurrent_pages tasks can enter this block at once
        async with self.semaphore:
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
                    logging.error("Cannot scrape: Scraper is closed")
                    raise RuntimeError(
                        "Scraper is closed. Create a new instance or use context manager."
                    )

                if self.session_data and not url.startswith(self.session_data.base_url):
                    logging.warning(
                        f"URL {url} does not match session base URL {self.session_data.base_url}. "
                        "Scraping may fail due to invalid session."
                    )

                self._validate_url(url=url)
                logging.info(f"Scraping: {url}")

                page = self._get_available_page()

                logging.debug(f"Navigating to: {url}")

                await page.goto(
                    url=url,
                    wait_until="networkidle",
                    timeout=timeout.total_seconds() * 1000,
                )
                logging.debug(f"Page loaded successfully: {url}")

                # Simple scroll to simulate human-like behavior (helps avoid bot detection)
                # Scrolling also helps trigger lazy-loaded content on pages that load data dynamically
                if self.browsing_mode == BrowsingMode.HUMAN_LIKE:
                    await self._apply_human_like_behavior(page)

                html_content = await page.content()
                elapsed_time = datetime.now(timezone.utc).timestamp() - sent_at
                logging.info(
                    f"Scraping finished: {url} in {elapsed_time:.2f}s with status={ScrapStatus.SUCCESS.value}"
                )
                self._record_event(sent_at=sent_at, status=ScrapStatus.SUCCESS)
                return ScrapeResponse(
                    scrape_request=scrape_request,
                    status=ScrapStatus.SUCCESS,
                    elapsed_time=elapsed_time,
                    scrap_html_content=html_content,
                )

            except PlaywrightTimeoutError as e:
                logging.warning(
                    f"Timeout while loading URL: {url}. "
                    f"Waited {timeout.total_seconds()} seconds. Returning partial content."
                )
                html_content = await page.content()
                elapsed_time = datetime.now(timezone.utc).timestamp() - sent_at
                self._record_event(sent_at=sent_at, status=ScrapStatus.PARTIAL_SUCCESS)
                logging.info(
                    f"Scraping finished: {url} in {elapsed_time:.2f}s with status={ScrapStatus.PARTIAL_SUCCESS.value}"
                )
                return ScrapeResponse(
                    scrape_request=scrape_request,
                    status=ScrapStatus.PARTIAL_SUCCESS,
                    elapsed_time=elapsed_time,
                    scrap_html_content=html_content,
                    error_msg=str(e),
                )

            except Exception as e:
                logging.error(f"Failed to scrape URL: {url}. Error: {e}", exc_info=True)
                self._record_event(sent_at=sent_at, status=ScrapStatus.FAILED)
                return ScrapeResponse(
                    scrape_request=scrape_request,
                    status=ScrapStatus.FAILED,
                    error_msg=str(e),
                )

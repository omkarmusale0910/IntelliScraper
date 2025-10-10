import json
import logging
import random
from datetime import timedelta
import copy
from playwright.sync_api import Page, TimeoutError, sync_playwright

from intelliscraper.common.constants import (
    BROWSER_LAUNCH_OPTIONS,
    DEFAULT_BROWSER_FINGERPRINT,
)
from intelliscraper.common.models import Proxy, Session
from intelliscraper.enums import BrowsingMode, HTMLParserType
from intelliscraper.exception import ScrapError
from intelliscraper.html_parser import HTMLParser


class Scraper:
    """A web scraper that retrieves HTML content from a given URL."""

    def __init__(
        self,
        headless: bool = True,
        open_new_page_per_scrape: bool = False,
        browser_launch_options: dict = BROWSER_LAUNCH_OPTIONS,
        proxy: Proxy | None = None,
        session_data: Session | None = None,
        browsing_mode: BrowsingMode | None = None,
        html_parser_type: HTMLParserType = HTMLParserType.HTML5LIB,
    ):
        """Initialize the scraper with browser and session configuration.

        Args:
            headless: Run browser without UI. Defaults to True.
            open_new_page_per_scrape: Open a new page for each scrape operation.
                Defaults to False.
            browser_launch_options: Custom Chromium launch options. Defaults to
                BROWSER_LAUNCH_OPTIONS.
            proxy: Proxy configuration for routing requests. Defaults to None.
            session_data: Pre-authenticated session containing cookies, localStorage,
                sessionStorage, and device fingerprint for bypassing login.
                Defaults to None.
            browsing_mode: Browsing behavior mode (FAST or HUMAN_LIKE). If not provided,
                automatically determined based on proxy/session_data presence.
                Defaults to None.
            html_parser_type: HTML parser to use (e.g., html5lib, lxml). Defaults to
                HTMLParserType.HTML5LIB.

        Note:
            - Browsing mode priority: If proxy is provided, defaults to FAST mode.
              If session_data is provided, defaults to HUMAN_LIKE mode.
            - Session data is essential for highly protected sites like LinkedIn...
        """
        logging.debug("Initializing Scraper")

        self.playwright = sync_playwright().start()
        self.open_new_page_per_scrape = open_new_page_per_scrape
        browser_launch_options = copy.deepcopy(browser_launch_options)
        browser_launch_options.update({"headless": headless})
        self.browser_launch_options = browser_launch_options
        self.html_parser_type = html_parser_type
        self.proxy = proxy
        self.session_data = session_data

        if proxy:
            logging.info(f"Using proxy: {proxy.server}")

        if session_data:
            logging.info("Using session data for authenticated scraping")

        self.browser = self.playwright.chromium.launch(**self.browser_launch_options)
        logging.debug(f"Browser launched with options {self.browser_launch_options}")
        browser_fingerprint = (
            self.session_data.fingerprint
            if self.session_data
            else DEFAULT_BROWSER_FINGERPRINT
        )
        self._create_browser_context(
            browser_fingerprint=browser_fingerprint, proxy=self.proxy
        )

        # Determine browsing mode based on priority
        # Priority logic:
        # - If a proxy is provided, it takes priority (use proxy).
        # - If no proxy but session data is provided, load session cookies and metadata into the context.
        # - If neither proxy nor session data is provided, start a fresh context.
        self.pages: list[Page] = []
        if browsing_mode:
            self.browsing_mode = browsing_mode
        elif self.proxy:
            self.browsing_mode = BrowsingMode.FAST
        elif self.session_data:
            self.browsing_mode = BrowsingMode.HUMAN_LIKE
        else:
            self.browsing_mode = BrowsingMode.HUMAN_LIKE

        logging.info(f"Scraper initialized with browsing mode: {self.browsing_mode}")

        self._add_cookies()
        self._apply_anti_detection_scripts()

    def _create_browser_context(
        self, browser_fingerprint: dict | None, proxy: Proxy | None
    ):
        """Create a browser context with fingerprint and proxy configuration."""
        logging.debug("Creating browser context")
        if browser_fingerprint is None:
            browser_fingerprint = DEFAULT_BROWSER_FINGERPRINT

        if proxy:
            proxy = proxy.model_dump()

        screen = browser_fingerprint.get("screenResolution", {})

        self.context = self.browser.new_context(
            # Screen & Viewport (from fingerprint)
            viewport={
                "width": screen.get("width", 1920),
                "height": screen.get("height", 1080),
            },
            screen={
                "width": screen.get("width", 1920),
                "height": screen.get("height", 1080),
            },
            proxy=proxy,
            geolocation={"latitude": 60, "longitude": 90},
            # Browser Identity (from fingerprint)
            user_agent=browser_fingerprint.get(
                "userAgent", "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
            ),
            # Locale & Timezone (from fingerprint)
            locale=browser_fingerprint.get("language", "en-US"),
            timezone_id=browser_fingerprint.get("timezone", "Asia/Calcutta"),
            # Device Settings
            device_scale_factor=1,
            is_mobile=False,
            has_touch=False,
            color_scheme="light",
            # Security
            ignore_https_errors=True,
            # Extra Headers
            extra_http_headers={
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Accept-Language": f"{browser_fingerprint.get("language", "en-US")},en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "DNT": "1",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            },
        )

    def _add_cookies(self):
        """Add cookies from session data to the browser context."""
        if self.session_data and self.session_data.cookies:
            logging.debug(f"Adding {len(self.session_data.cookies)} cookies")
            self.context.add_cookies(self.session_data.cookies)

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

    def __del__(self):
        """Cleanup on destruction."""
        try:
            self.context.close()
            self.browser.close()
            self.playwright.stop()
            logging.debug("Cleanup complete")
        except Exception:
            pass

    def _get_page(self) -> Page:
        """Get or create a page instance with session storage applied.

        Returns:
            Page: A Playwright page instance.
        """
        if not self.pages:
            logging.debug("Creating new page")
            page = self.context.new_page()
            # Required for BOTH storage types
            if self.session_data and (
                self.session_data.localStorage or self.session_data.sessionStorage
            ):
                logging.debug("Applying session | local storage")
                page.goto(self.session_data.base_url)
                if self.session_data.localStorage:
                    page.evaluate(
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
                    page.evaluate(
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
            self.pages.append(page)
            return page

        if self.open_new_page_per_scrape:
            logging.debug(f"Creating new page (total: {len(self.pages) + 1})")
            # Once we have added local and session storage,
            # it will be per context basis, so for every new page,
            # we don't need to add this local and session storage;
            # only once is required.
            page = self.context.new_page()
            self.pages.append(page)

        return self.pages[-1]

    def scrap(self, url: str, timeout: timedelta = timedelta(seconds=30)) -> HTMLParser:
        """Navigate to the given URL and return the page content.

        Args:
            url (str): The target URL to scrape.
            timeout (timedelta, optional): Maximum wait time for page load.
                                           Defaults to 30 seconds.

        Returns:
            str: The HTML content of the page, even if a timeout occurs.

        Raises:
            ScrapError: If scraping fails due to an unexpected error.

        Note:
            - Returns partial content if timeout occurs during loading.
            - Applies human-like scrolling behavior when browsing_mode is HUMAN_LIKE.
            - For custom behavior (advanced scrolling, mouse movements), extend this class.
        """
        logging.info(f"Scraping: {url}")
        page = self._get_page()
        try:
            page.goto(
                url=url,
                wait_until="networkidle",
                timeout=timeout.total_seconds() * 1000,
            )
            logging.debug(f"Page loaded: {url}")
            # Optional: Add extra waiting if needed
            # Use wait_for_selector() if you need to wait for a specific element to appear on the page
            # Example: page.wait_for_selector(".product-list", timeout=60000)
            #
            # Use wait_for_timeout() if you need to wait for a fixed amount of time
            # Example: page.wait_for_timeout(60000)  # waits 60 seconds

            # Note: This class provides basic page loading functionality.
            # If you need human-like behavior (such as scrolling, mouse movements, or random delays),
            # you can extend this class and add those features in your implementation.

            # Simple scroll to simulate human-like behavior (helps avoid bot detection)
            # Scrolling also helps trigger lazy-loaded content on pages that load data dynamically
            if self.browsing_mode == BrowsingMode.HUMAN_LIKE:
                page.evaluate(
                    """
                    window.scrollTo({
                        top: document.body.scrollHeight / 2,
                        behavior: 'smooth'
                    });
                """
                )
                page.wait_for_timeout(random.uniform(500, 1500))

            # Note: This class provides basic page loading with optional simple scrolling.
            # For advanced anti-detection features, extend this class and implement:
            # - Random scrolling patterns
            # - Mouse movements and hovering
            # - Variable delays between actions
            # - Click interactions with elements
            # These techniques help avoid bot detection on sites with advanced security.
            logging.info(f"Successfully scraped: {url}")
            return HTMLParser(
                base_url=url,
                html=page.content(),
                html_parser_type=self.html_parser_type,
            )
        except TimeoutError:
            logging.warning(
                f"Timeout while loading URL: {url}. "
                f"Waited {timeout.total_seconds()} seconds. Returning partial content."
            )
            return HTMLParser(
                base_url=url,
                html=page.content(),
                html_parser_type=self.html_parser_type,
            )
        except Exception as e:
            logging.error(f"Failed to scrape URL: {url}. Error: {e}", exc_info=True)
            raise ScrapError(f"Scraping failed for URL: {url}") from e

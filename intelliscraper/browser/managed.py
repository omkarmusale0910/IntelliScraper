"""Managed browser backend launches Chromium via Playwright.

Launches a fresh Chromium instance managed entirely by the scraper.
Applies fingerprint spoofing, proxy configuration, anti-detection
scripts, and session cookies/storage when provided.

This is the default backend used when ``use_local_browser=False``.
"""

from __future__ import annotations

import json
import logging
import random
from typing import TYPE_CHECKING

from intelliscraper.browser.backend import BrowserBackend
from intelliscraper.common.constants import (
    BROWSER_LAUNCH_OPTIONS,
    DEFAULT_BROWSER_FINGERPRINT,
)
from intelliscraper.common.models import Proxy, Session

if TYPE_CHECKING:
    from playwright.async_api import Browser, BrowserContext, Playwright

logger = logging.getLogger(__name__)


class ManagedBrowserBackend(BrowserBackend):
    """Launch and manage a Chromium browser instance via Playwright.

    Handles the full lifecycle of a Playwright-managed browser:
    launching, configuring the context (fingerprint, proxy, cookies,
    anti-detection scripts), and tearing everything down on cleanup.

    Args:
        headless: Run browser without a visible UI.  Defaults to
            ``True``.
        browser_launch_options: Custom Chromium launch options.  Merged
            with the ``headless`` flag.  Defaults to
            ``BROWSER_LAUNCH_OPTIONS``.
        proxy: Proxy configuration for network requests.  Applied at
            the browser-context level so all pages share the same
            proxy.  Defaults to ``None``.
        session_data: Pre-authenticated session with cookies,
            localStorage, sessionStorage, and browser fingerprint.
            Defaults to ``None``.

    Example::

        backend = ManagedBrowserBackend(
            headless=True,
            proxy=my_proxy,
            session_data=my_session,
        )
        browser, context = await backend.initialize(playwright)
    """

    def __init__(
        self,
        headless: bool = True,
        browser_launch_options: dict | None = None,
        proxy: Proxy | None = None,
        session_data: Session | None = None,
    ) -> None:
        self._headless = headless
        self._launch_options = dict(browser_launch_options or BROWSER_LAUNCH_OPTIONS)
        self._launch_options["headless"] = headless
        self._proxy = proxy
        self._session_data = session_data

    @property
    def owns_browser(self) -> bool:
        """Managed backend owns and should close the browser process."""
        return True

    async def initialize(
        self,
        playwright: Playwright,
    ) -> tuple[Browser, BrowserContext]:
        """Launch Chromium and create a fully configured context.

        Steps performed:

        1. Launch Chromium with the configured options.
        2. Create a browser context with fingerprint spoofing and
           optional proxy.
        3. Inject session cookies (if provided).
        4. Apply anti-detection JavaScript scripts.

        Args:
            playwright: A started Playwright instance.

        Returns:
            A ``(browser, context)`` tuple.
        """
        logger.debug("Launching browser with options: %s", self._launch_options)
        browser = await playwright.chromium.launch(**self._launch_options)
        logger.debug("Browser launched successfully")

        fingerprint = (
            self._session_data.fingerprint
            if self._session_data
            else DEFAULT_BROWSER_FINGERPRINT
        )
        context = await self._create_browser_context(
            browser=browser,
            fingerprint=fingerprint,
        )
        await self._add_cookies(context)
        self._apply_anti_detection_scripts(context, fingerprint)

        logger.info("Managed browser ready.")
        return browser, context

    async def cleanup(
        self,
        browser: Browser,
        context: BrowserContext,
    ) -> None:
        """Close context and browser process.

        Args:
            browser: The Playwright-managed browser to close.
            context: The browser context to close.
        """
        if context:
            await context.close()
            logger.debug("Browser context closed.")
        if browser:
            await browser.close()
            logger.debug("Browser process closed.")

    async def apply_session_storage(
        self,
        page,
    ) -> None:
        """Apply localStorage and sessionStorage to a page.

        If ``session_data`` is configured with storage data, navigates
        the page to the session's ``base_url`` and injects the stored
        key-value pairs.

        Args:
            page: A Playwright ``Page`` instance to configure.
        """
        if not self._session_data:
            return
        if not (self._session_data.localStorage or self._session_data.sessionStorage):
            return

        logger.debug("Applying session / local storage")
        await page.goto(self._session_data.base_url)

        if self._session_data.localStorage:
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
                self._session_data.localStorage,
            )

        if self._session_data.sessionStorage:
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
                self._session_data.sessionStorage,
            )
        logger.debug("Session storage applied successfully")

    async def _create_browser_context(
        self,
        browser: Browser,
        fingerprint: dict | None,
    ) -> BrowserContext:
        """Create a browser context with fingerprint and proxy config.

        Args:
            browser: The launched browser instance.
            fingerprint: Browser fingerprint dict for anti-detection.

        Returns:
            A configured ``BrowserContext``.
        """
        logger.debug("Creating browser context")
        if fingerprint is None:
            fingerprint = DEFAULT_BROWSER_FINGERPRINT

        proxy_dict = self._proxy.model_dump() if self._proxy else None
        screen = fingerprint.get("screenResolution", {})

        context = await browser.new_context(
            viewport={
                "width": screen.get("width", 1920),
                "height": screen.get("height", 1080),
            },
            screen={
                "width": screen.get("width", 1920),
                "height": screen.get("height", 1080),
            },
            proxy=proxy_dict,
            geolocation={
                "latitude": random.uniform(-90, 90),
                "longitude": random.uniform(-180, 180),
            },
            user_agent=fingerprint.get(
                "userAgent",
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
            ),
            locale=fingerprint.get("language", "en-US"),
            timezone_id=fingerprint.get("timezone", "Asia/Calcutta"),
            device_scale_factor=1,
            is_mobile=False,
            has_touch=False,
            color_scheme="light",
            ignore_https_errors=True,
            extra_http_headers={
                "Accept": (
                    "text/html,application/xhtml+xml,application/xml;"
                    "q=0.9,image/avif,image/webp,*/*;q=0.8"
                ),
                "Accept-Language": (f"{fingerprint.get('language', 'en-US')},en;q=0.9"),
                "Accept-Encoding": "gzip, deflate, br",
                "DNT": "1",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            },
        )
        logger.debug("Browser context created successfully")
        return context

    async def _add_cookies(self, context: BrowserContext) -> None:
        """Add cookies from session data to the browser context.

        Args:
            context: The browser context to add cookies to.
        """
        if self._session_data and self._session_data.cookies:
            logger.debug("Adding %d cookies", len(self._session_data.cookies))
            await context.add_cookies(self._session_data.cookies)
            logger.debug("Cookies added successfully")

    def _apply_anti_detection_scripts(
        self,
        context: BrowserContext,
        fingerprint: dict | None,
    ) -> None:
        """Inject JavaScript to mask automation and avoid bot detection.

        Spoofs ``navigator.webdriver``, plugins, languages, hardware
        concurrency, device memory, platform, screen properties, and
        WebGL renderer strings.

        Args:
            context: The browser context to inject scripts into.
            fingerprint: Browser fingerprint dict with values to spoof.
        """
        logger.debug("Applying anti-detection scripts")
        if fingerprint is None:
            fingerprint = DEFAULT_BROWSER_FINGERPRINT

        context.add_init_script(
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
                get: () => {json.dumps(fingerprint.get('languages', ['en-US']))}
            }});

            // Hardware (from fingerprint)
            Object.defineProperty(navigator, 'hardwareConcurrency', {{
                get: () => {fingerprint.get('hardwareConcurrency', 8)}
            }});

            Object.defineProperty(navigator, 'deviceMemory', {{
                get: () => {fingerprint.get('deviceMemory', 8)}
            }});

            Object.defineProperty(navigator, 'platform', {{
                get: () => "{fingerprint.get('platform', 'Linux x86_64')}"
            }});

            // Screen properties
            Object.defineProperty(screen, 'colorDepth', {{
                get: () => {fingerprint.get("screenResolution", {{}}).get('colorDepth', 24)}
            }});

            Object.defineProperty(screen, 'pixelDepth', {{
                get: () => {fingerprint.get("screenResolution", {{}}).get('colorDepth', 24)}
            }});

            // WebGL (from fingerprint)
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {{
                if (parameter === 37445) {{
                    return "{fingerprint.get('webglVendor', 'Google Inc. (Intel)')}";
                }}
                if (parameter === 37446) {{
                    return "{fingerprint.get('webglRenderer', 'ANGLE (Intel)')}";
                }}
                return getParameter.call(this, parameter);
            }};
        """
        )
        logger.debug("Anti-detection scripts applied")

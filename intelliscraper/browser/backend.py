"""Abstract base class for browser backends.

All browser lifecycle management starting, configuring, and tearing
down the browser is handled through this interface.  ``AsyncScraper``
delegates to a concrete backend chosen at construction time.
"""

from __future__ import annotations

import abc
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.async_api import Browser, BrowserContext, Playwright


class BrowserBackend(abc.ABC):
    """Abstract base for browser lifecycle management.

    Subclasses handle how a browser is started, configured, and cleaned
    up.  The scraper delegates all browser-level concerns here.

    Typical usage::

        backend = ManagedBrowserBackend(headless=True, ...)
        browser, context = await backend.initialize(playwright)
        # ... use browser / context ...
        await backend.cleanup(browser, context)
    """

    @abc.abstractmethod
    async def initialize(
        self,
        playwright: Playwright,
    ) -> tuple[Browser, BrowserContext]:
        """Start the browser and return a ready-to-use context.

        Args:
            playwright: A started Playwright instance.

        Returns:
            A ``(browser, context)`` tuple.

        Raises:
            LocalBrowserConnectionError: If the local browser cannot be
                reached (only from ``LocalBrowserBackend``).
        """

    @abc.abstractmethod
    async def cleanup(
        self,
        browser: Browser,
        context: BrowserContext,
    ) -> None:
        """Release browser resources.

        What gets closed depends on the backend:

        * **Local**: Only the pages opened by the scraper are closed.
          The Chrome process and its context are left running.
        * **Managed**: Pages, context, and browser process are all
          closed.

        Args:
            browser: The browser instance to clean up.
            context: The browser context to clean up.
        """

    @property
    @abc.abstractmethod
    def owns_browser(self) -> bool:
        """Whether this backend owns (and should close) the browser process.

        Returns:
            ``True`` for managed backends, ``False`` for local/CDP
            backends where the browser belongs to the user.
        """

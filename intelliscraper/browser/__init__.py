"""Browser backend implementations for IntelliScraper.

Provides the Strategy pattern for browser lifecycle management.
Two backends are available:

- ``LocalBrowserBackend``: Connects to an already-running Chrome instance
  via CDP on port 9222.  All existing cookies, logins, and sessions are
  immediately available.
- ``ManagedBrowserBackend``: Launches a fresh Chromium instance managed
  entirely by the scraper.  Applies fingerprint spoofing, proxy, and
  session cookies.
"""

from intelliscraper.browser.backend import BrowserBackend
from intelliscraper.browser.local import LocalBrowserBackend
from intelliscraper.browser.managed import ManagedBrowserBackend

__all__ = [
    "BrowserBackend",
    "LocalBrowserBackend",
    "ManagedBrowserBackend",
]

"""IntelliScraper — Advanced async web scraping library.

A modern web scraping library built on Playwright with support for:

- Two browser modes: local Chrome (CDP) and managed Chromium.
- Session management for authenticated scraping.
- Anti-detection techniques (fingerprint spoofing, stealth scripts).
- Token-bucket rate limiting shared across concurrent pages.
- Batch scraping with ``batch_scrape()``.
- Extensible content parsers (HTML, custom).
- Proxy integration (Bright Data, custom providers).
"""

from intelliscraper.browser import (
    BrowserBackend,
    LocalBrowserBackend,
    ManagedBrowserBackend,
)
from intelliscraper.common.constants import (
    BROWSER_LAUNCH_OPTIONS,
    DEFAULT_BROWSER_FINGERPRINT,
)
from intelliscraper.common.models import (
    Proxy,
    ScrapeRequest,
    ScrapeResponse,
    Session,
)
from intelliscraper.enums import BrowsingMode, HTMLParserType, ScrapStatus
from intelliscraper.exception import (
    BotDetectionError,
    HTMLParserInputError,
    LocalBrowserConnectionError,
    RateLimitExceededError,
    ScraperNotInitializedError,
)
from intelliscraper.parsers import BaseParser, HTMLParser
from intelliscraper.proxy.base import ProxyProvider
from intelliscraper.proxy.brightdata import BrightDataProxy
from intelliscraper.rate_limiter import RateLimiter
from intelliscraper.scraper import AsyncScraper

__all__ = [
    # Core
    "AsyncScraper",
    # Browser backends
    "BrowserBackend",
    "LocalBrowserBackend",
    "ManagedBrowserBackend",
    # Parsers
    "BaseParser",
    "HTMLParser",
    # Rate limiting
    "RateLimiter",
    # Models
    "Proxy",
    "Session",
    "ScrapeRequest",
    "ScrapeResponse",
    # Enums
    "BrowsingMode",
    "HTMLParserType",
    "ScrapStatus",
    # Proxy
    "ProxyProvider",
    "BrightDataProxy",
    # Exceptions
    "HTMLParserInputError",
    "LocalBrowserConnectionError",
    "ScraperNotInitializedError",
    "RateLimitExceededError",
    "BotDetectionError",
    # Constants
    "BROWSER_LAUNCH_OPTIONS",
    "DEFAULT_BROWSER_FINGERPRINT",
]

"""IntelliScraper - Advanced web scraping library.

A modern web scraping library built on Playwright with support for:
- Session management for authenticated scraping
- Anti-detection techniques
- Human-like browsing behavior
- Proxy integration (BrightData Proxy,...)
"""

from intelliscraper.common.constants import (
    BROWSER_LAUNCH_OPTIONS,
    DEFAULT_BROWSER_FINGERPRINT,
)
from intelliscraper.common.models import Proxy, ScrapeRequest, ScrapeResponse, Session
from intelliscraper.enums import BrowsingMode, HTMLParserType, ScrapStatus
from intelliscraper.exception import HTMLParserInputError
from intelliscraper.html_parser import HTMLParser
from intelliscraper.proxy.base import ProxyProvider
from intelliscraper.proxy.brightdata import BrightDataProxy
from intelliscraper.scraper import Scraper

__all__ = [
    # Core
    "Scraper",
    "HTMLParser",
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
    # constants
    "BROWSER_LAUNCH_OPTIONS",
    "DEFAULT_BROWSER_FINGERPRINT",
]

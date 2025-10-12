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
from intelliscraper.common.models import Proxy, Session
from intelliscraper.enums import BrowsingMode, HTMLParserType
from intelliscraper.exception import HTMLParserInputError, ScrapError
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
    # Enums
    "BrowsingMode",
    "HTMLParserType",
    # Proxy
    "ProxyProvider",
    "BrightDataProxy",
    # Exceptions
    "ScrapError",
    "HTMLParserInputError",
    # constants
    "BROWSER_LAUNCH_OPTIONS",
    "DEFAULT_BROWSER_FINGERPRINT",
]

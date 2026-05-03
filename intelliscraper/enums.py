"""Enumerations used throughout IntelliScraper."""

from enum import Enum


class HTMLParserType(str, Enum):
    """Supported HTML parser backends for ``HTMLParser``.

    Determines which parser engine BeautifulSoup uses under the hood.

    Attributes:
        HTML5LIB: Full HTML5 parsing (most accurate, slower).
        BUILTIN: Python's built-in ``html.parser`` (faster, less
            forgiving).
    """

    HTML5LIB = "html5lib"
    BUILTIN = "html.parser"


class BrowsingMode(str, Enum):
    """Defines how the browser behaves during scraping.

    Attributes:
        HUMAN_LIKE: Adds delays, scrolling, and randomness to mimic
            human browsing.  Recommended when using session data or
            scraping protected sites.
        FAST: Minimal delays, optimised for throughput.  Recommended
            when using a proxy for identity rotation.
    """

    HUMAN_LIKE = "human_like"
    FAST = "fast"


class ScrapStatus(str, Enum):
    """Outcome status of a scraping operation.

    Attributes:
        SUCCESS: Page loaded fully and content was extracted.
        PARTIAL_SUCCESS: Page timed out but partial content was
            retrieved.
        FAILED: An error prevented content extraction.
        RATE_LIMITED: Server returned HTTP 429 Too Many Requests.
        BLOCKED: Bot detection was triggered (HTTP 403 + known
            patterns).
        TIMEOUT: Page load timed out with no usable content.
    """

    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILED = "failed"
    RATE_LIMITED = "rate_limited"
    BLOCKED = "blocked"
    TIMEOUT = "timeout"

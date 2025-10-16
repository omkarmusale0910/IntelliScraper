from enum import Enum


class HTMLParserType(str, Enum):
    """
    Enum representing supported HTML parsers for HTMLParser.
    """

    HTML5LIB = "html5lib"
    BUILTIN = "html.parser"


class BrowsingMode(str, Enum):
    """
    Defines how the browser behaves during scraping.

    - HUMAN_LIKE: Used when session data is provided or no proxy is used.
      Adds delays, randomness, and mimics human browsing behavior.

    - FAST: Used when a proxy is provided.
      Focuses on speed, minimal delay, and optimized for large-scale scraping.
    """

    HUMAN_LIKE = "human_like"
    FAST = "fast"


class ScrapStatus(str, Enum):
    """Represents the status of a scraping operation."""

    PARTIAL = "partial"
    COMPLETED = "completed"
    FAILED = "failed"

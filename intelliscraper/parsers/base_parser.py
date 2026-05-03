"""Abstract base class for content parsers.

All parsers in IntelliScraper extend ``BaseParser`` to provide a
consistent interface for extracting text, links, and Markdown from
scraped HTML content.

To create a site-specific parser, subclass ``HTMLParser`` (which
already implements ``BaseParser``) and add your custom extraction
logic as ``@cached_property`` methods.

Example::

    class MyCustomParser(HTMLParser):
        @cached_property
        def product_title(self) -> str | None:
            tag = self.soup.select_one("h1.product-title")
            return tag.get_text(strip=True) if tag else None
"""

from __future__ import annotations

import abc
from functools import cached_property


class BaseParser(abc.ABC):
    """Abstract base for all content parsers.

    Defines the minimum interface that every parser must implement.
    Concrete parsers should extend ``HTMLParser`` rather than this
    class directly, unless they need a fundamentally different
    parsing engine.

    Args:
        url: The source URL of the scraped page.  Used for
            normalising relative links.
        html: Raw HTML string to parse.
    """

    @abc.abstractmethod
    def __init__(self, url: str, html: str) -> None:
        """Initialize the parser with URL and HTML content."""

    @cached_property
    @abc.abstractmethod
    def text(self) -> str:
        """Extract plain text from the HTML content."""

    @cached_property
    @abc.abstractmethod
    def links(self) -> list[str]:
        """Extract all normalised ``href`` values from ``<a>`` tags."""

    @cached_property
    @abc.abstractmethod
    def markdown(self) -> str:
        """Convert the HTML to Markdown."""

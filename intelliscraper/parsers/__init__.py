"""Content parsers for IntelliScraper.

Provides a hierarchy of parsers for extracting structured data from
scraped HTML:

- ``BaseParser``: Abstract base defining the parser interface.
- ``HTMLParser``: General-purpose HTML → text / links / Markdown.
"""

from intelliscraper.parsers.base_parser import BaseParser
from intelliscraper.parsers.html_parser import HTMLParser

__all__ = [
    "BaseParser",
    "HTMLParser",
]

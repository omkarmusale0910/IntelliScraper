"""Content parsers for IntelliScraper.

Provides a hierarchy of parsers for extracting structured data from
scraped HTML:

- ``BaseParser``: Abstract base defining the parser interface.
- ``HTMLParser``: General-purpose HTML → text / links / Markdown.
- ``LinkedInJobPageParser``: LinkedIn job-page specific extraction
  (skeleton — extend with site-specific selectors).
"""

from intelliscraper.parsers.base_parser import BaseParser
from intelliscraper.parsers.html_parser import HTMLParser
from intelliscraper.parsers.linkedin_parser import LinkedInJobPageParser

__all__ = [
    "BaseParser",
    "HTMLParser",
    "LinkedInJobPageParser",
]

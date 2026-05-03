"""General-purpose HTML parser.

Parses raw HTML content and provides access to plain text, links,
Markdown, and LLM-optimised Markdown (with boilerplate stripped).

This is the default parser used by IntelliScraper and the recommended
base class for site-specific parsers.

Example::

    parser = HTMLParser(url="https://example.com", html=html_string)
    print(parser.text)               # plain text
    print(parser.links)              # list of absolute URLs
    print(parser.markdown)           # full Markdown
    print(parser.markdown_for_llm)   # cleaned Markdown for LLM input
    print(parser.navigable_links)    # classified internal/external links
"""

from __future__ import annotations

from functools import cached_property

from bs4 import BeautifulSoup
from html_to_markdown import LinkType
from html_to_markdown.api import convert as _convert
from html_to_markdown.options import PreprocessingOptions

from intelliscraper.enums import HTMLParserType
from intelliscraper.exception import HTMLParserInputError
from intelliscraper.parsers.base_parser import BaseParser
from intelliscraper.utils import normalize_links

# ---------------------------------------------------------------------------
# html-to-markdown v3.x exposes ConversionOptions as an immutable Rust type
# with a broken Python constructor.  The public api.py wrapper accepts any
# object with the right string attributes, so we use a plain class instead.
# ---------------------------------------------------------------------------


class _ConversionOpts:
    """Duck-typed ``ConversionOptions`` for ``html_to_markdown.api.convert``."""

    def __init__(
        self,
        preprocessing: PreprocessingOptions | None = None,
        extract_metadata: bool = True,
    ) -> None:
        self.heading_style = "atx"
        self.list_indent_type = "spaces"
        self.list_indent_width = 2
        self.bullets = "-*+"
        self.strong_em_symbol = "*"
        self.escape_asterisks = False
        self.escape_underscores = False
        self.escape_misc = False
        self.escape_ascii = False
        self.code_language = ""
        self.autolinks = True
        self.default_title = False
        self.br_in_tables = False
        self.highlight_style = "double_equal"
        self.extract_metadata = extract_metadata
        self.whitespace_mode = "normalized"
        self.strip_newlines = False
        self.wrap = False
        self.wrap_width = 80
        self.convert_as_inline = False
        self.sub_symbol = ""
        self.sup_symbol = ""
        self.newline_style = "spaces"
        self.code_block_style = "backticks"
        self.keep_inline_images_in = []
        self.preprocessing = preprocessing
        self.encoding = "utf-8"
        self.debug = False
        self.strip_tags = []
        self.preserve_tags = []
        self.skip_images = False
        self.link_style = "inline"
        self.output_format = "markdown"
        self.include_document_structure = False
        self.extract_images = False
        self.max_image_size = 5_242_880
        self.capture_svg = False
        self.infer_dimensions = True
        self.max_depth = None
        self.exclude_selectors = []


_OPTS_STANDARD = _ConversionOpts(
    preprocessing=PreprocessingOptions(
        enabled=True,
        preset="standard",
        remove_navigation=False,
        remove_forms=False,
    ),
    extract_metadata=True,
)

_OPTS_LLM = _ConversionOpts(
    preprocessing=PreprocessingOptions(
        enabled=True,
        preset="aggressive",
        remove_navigation=True,
        remove_forms=True,
    ),
    extract_metadata=False,
)


class HTMLParser(BaseParser):
    """General-purpose HTML parser with text, link, and Markdown extraction.

    Wraps BeautifulSoup for DOM querying and ``html-to-markdown`` for
    Markdown conversion.  Provides both standard and LLM-optimised
    Markdown outputs.

    All properties are lazily computed and cached on first access.

    Args:
        url: The source URL of the page (used for link normalisation).
        html: Raw HTML string.  Must be a non-empty string.
        html_parser_type: BeautifulSoup parser backend.  Defaults to
            ``HTMLParserType.HTML5LIB``.

    Raises:
        HTMLParserInputError: If ``html`` is empty or not a string.

    Example::

        parser = HTMLParser(
            url="https://example.com/page",
            html=response.scrap_html_content,
        )
        print(parser.text)
        print(parser.links)
        print(parser.markdown_for_llm)
    """

    def __init__(
        self,
        url: str,
        html: str,
        html_parser_type: HTMLParserType = HTMLParserType.HTML5LIB,
    ) -> None:
        if not (html and isinstance(html, str)):
            raise HTMLParserInputError(
                "HTMLParser expects a non-empty string as HTML input."
            )
        self.url = url
        self.html = html
        self.soup = BeautifulSoup(html, html_parser_type.value)

    @cached_property
    def _conversion_result(self):
        """Single conversion shared by ``markdown`` and ``navigable_links``."""
        return _convert(self.html, _OPTS_STANDARD)

    @cached_property
    def text(self) -> str:
        """Plain text extracted from the HTML.

        Uses BeautifulSoup's ``get_text()`` with newline separators and
        whitespace stripping.
        """
        return self.soup.get_text(separator="\n", strip=True)

    @cached_property
    def links(self) -> list[str]:
        """All normalised ``href`` values from ``<a>`` tags.

        Relative URLs are resolved against the source URL.  Duplicates
        and fragment-only links are removed.

        Returns:
            A deduplicated list of absolute HTTP/HTTPS URLs.
        """
        all_links = [a.get("href") for a in self.soup.find_all("a") if a.get("href")]
        return normalize_links(base_url=self.url, links=all_links)

    @cached_property
    def navigable_links(self) -> list[dict]:
        """Internal and external page links, classified and normalised.

        Skips anchors (``#fragment``), ``mailto:``, ``tel:``,
        ``javascript:``, and resource links (CSS/JS).

        Returns:
            A list of dicts, each with keys:

            - ``href`` — absolute URL
            - ``text`` — visible link label
            - ``title`` — title attribute or ``None``
            - ``link_type`` — ``"Internal"`` or ``"External"``
            - ``rel`` — list of rel values (e.g. ``["nofollow"]``)
        """
        raw_links = self._conversion_result.metadata.links or []
        result = []
        for link in raw_links:
            if link.link_type not in (
                LinkType.Internal,
                LinkType.External,
            ):
                continue
            href = (link.href or "").strip()
            if not href:
                continue
            normalised = normalize_links(base_url=self.url, links=[href])
            if not normalised:
                continue
            result.append(
                {
                    "href": normalised[0],
                    "text": (link.text or "").strip(),
                    "title": link.title,
                    "link_type": str(link.link_type).split(".")[-1],
                    "rel": list(link.rel or []),
                }
            )
        return result

    @cached_property
    def markdown(self) -> str:
        """Full-page Markdown with standard preprocessing.

        Preserves navigation, forms, and page structure.
        """
        return self._conversion_result.content or ""

    @cached_property
    def markdown_for_llm(self) -> str:
        """Markdown with nav, ads, forms, and boilerplate stripped.

        Optimised for use as LLM input — removes elements that add
        noise without informational value.
        """
        return _convert(self.html, _OPTS_LLM).content or ""

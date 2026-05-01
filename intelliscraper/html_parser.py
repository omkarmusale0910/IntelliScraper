from functools import cached_property

from bs4 import BeautifulSoup
from html_to_markdown import LinkType
from html_to_markdown.api import convert as _convert
from html_to_markdown.options import PreprocessingOptions

from intelliscraper.enums import HTMLParserType
from intelliscraper.exception import HTMLParserInputError
from intelliscraper.utils import normalize_links

# ---------------------------------------------------------------------------
# html-to-markdown v3.x exposes ConversionOptions as an immutable Rust type
# with a broken Python constructor. The public api.py wrapper accepts any
# object with the right string attributes, so we use a plain class instead.
# ---------------------------------------------------------------------------


class _Opts:
    """Duck-typed ConversionOptions for html_to_markdown.api.convert."""

    def __init__(
        self,
        preprocessing: PreprocessingOptions | None = None,
        extract_metadata: bool = True,
    ):
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


_OPTS_STANDARD = _Opts(
    preprocessing=PreprocessingOptions(
        enabled=True,
        preset="standard",
        remove_navigation=False,
        remove_forms=False,
    ),
    extract_metadata=True,
)

_OPTS_LLM = _Opts(
    preprocessing=PreprocessingOptions(
        enabled=True,
        preset="aggressive",
        remove_navigation=True,
        remove_forms=True,
    ),
    extract_metadata=False,
)


class HTMLParser:
    """Parses HTML content and extracts text, links, and Markdown."""

    def __init__(
        self,
        url: str,
        html: str,
        html_parser_type: HTMLParserType = HTMLParserType.HTML5LIB,
    ):
        self.url = url
        if not (html and isinstance(html, str)):
            raise HTMLParserInputError(
                "HTMLParser expects a non-empty string as HTML input."
            )
        self.html = html
        self.soup = BeautifulSoup(html, html_parser_type.value)

    @cached_property
    def _conversion_result(self):
        """Single conversion shared by `markdown` and `navigable_links`."""
        return _convert(self.html, _OPTS_STANDARD)

    @cached_property
    def text(self) -> str:
        """Plain text extracted from the HTML."""
        return self.soup.get_text(separator="\n", strip=True)

    @cached_property
    def links(self) -> list[str]:
        """All normalised hrefs from <a> tags (existing behaviour)."""
        all_links = [a.get("href") for a in self.soup.find_all("a") if a.get("href")]
        return normalize_links(base_url=self.url, links=all_links)

    @cached_property
    def navigable_links(self) -> list[dict]:
        """Internal and external page links, classified and normalised.

        Skips anchors (#fragment), mailto:, tel:, javascript:, and
        resource links (CSS/JS). Each entry has:
            href      — absolute URL
            text      — visible link label
            title     — title attribute or None
            link_type — "Internal" or "External"
            rel       — list of rel values e.g. ["nofollow"]
        """
        raw_links = self._conversion_result.metadata.links or []
        result = []
        for link in raw_links:
            if link.link_type not in (LinkType.Internal, LinkType.External):
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
        """Full-page Markdown with standard preprocessing."""
        return self._conversion_result.content or ""

    @cached_property
    def markdown_for_llm(self) -> str:
        """Markdown with nav, ads, forms, and boilerplate stripped."""
        return _convert(self.html, _OPTS_LLM).content or ""

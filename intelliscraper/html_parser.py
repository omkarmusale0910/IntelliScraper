from functools import cached_property

from bs4 import BeautifulSoup

from intelliscraper.enums import HTMLParserType
from intelliscraper.exception import HTMLParserInputError
from intelliscraper.utils import normalize_links


class HTMLParser:
    """
    A utility class for parsing HTML content and extracting information.

    This class allows extraction of:
    - Plain text from HTML
    - All hyperlinks in the HTML
    - (Optional extension: Markdown conversion)

    """

    def __init__(
        self,
        base_url: str,
        html: str,
        html_parser: HTMLParserType = HTMLParserType.HTML5LIB,
    ):
        """
        Initialize the HTMLParser with raw HTML content.

        Args:
            html (str): The HTML content to parse.
            html_parser (HTMLParserType): The parser to use (default: "html5lib").
        """
        self.base_url = base_url
        if not (html and isinstance(html, str)):
            raise HTMLParserInputError(
                "HTMLParser expects a non-empty string as HTML input."
            )
        self.html = html
        self.soup = BeautifulSoup(html, html_parser.value)

    @cached_property
    def text(self) -> str:
        """
        Extract plain text from the HTML content.

        Returns:
            str: Text content of the HTML.
        """

        return self.soup.get_text(separator="\n", strip=True)

    @cached_property
    def links(self) -> list[str]:
        """
        Extract all hyperlinks from the HTML content.

        Returns:
            list[str]: List of all 'href' attributes found in <a> tags.
        """
        all_links = [a.get("href") for a in self.soup.find_all("a") if a.get("href")]
        return normalize_links(base_url=self.base_url, links=all_links)

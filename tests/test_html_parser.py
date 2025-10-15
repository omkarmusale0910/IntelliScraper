import os

import pytest

from intelliscraper.html_parser import HTMLParser

TEST_DIR = os.path.dirname(__file__)

# Test data extracted from: https://www.iana.org/help/example-domain
SCRAP_HTML_DATA_FILEPATH_1 = os.path.join(TEST_DIR, "testdata/scrap_data_1.html")

# Test data extracted from: https://www.iana.org/domains
SCRAP_HTML_DATA_FILEPATH_2 = os.path.join(TEST_DIR, "testdata/scrap_data_2.html")

MARKDOWN_PARSED_DATA_FOR_DATA_1 = os.path.join(
    TEST_DIR, "testdata/markdown/scrap_data_1.md"
)


@pytest.fixture(scope="class")
def scrap_html_data() -> dict:
    """Fixture that loads all test HTML files into memory once per test class.
    Returns a dictionary mapping file paths to their HTML content.
    """
    test_filepaths = [SCRAP_HTML_DATA_FILEPATH_1, SCRAP_HTML_DATA_FILEPATH_2]
    test_html_data = {}
    for test_filepath in test_filepaths:
        with open(test_filepath, "r") as f:
            html_content = f.read()
            test_html_data[str(test_filepath)] = html_content
    return test_html_data


class TestHTMLParser:

    @pytest.mark.parametrize(
        "filepath,base_url,expected_links",
        [
            (
                SCRAP_HTML_DATA_FILEPATH_1,
                "https://www.iana.org/help/example-domains",
                [
                    "https://www.iana.org/",
                    "https://www.iana.org/domains",
                    "https://www.iana.org/protocols",
                    "https://www.iana.org/numbers",
                    "https://www.iana.org/about",
                    "https://www.iana.org/go/rfc2606",
                    "https://www.iana.org/go/rfc6761",
                    "https://www.iana.org/domains/reserved",
                    "https://www.iana.org/domains/root",
                    "https://www.iana.org/domains/int",
                    "https://www.iana.org/domains/arpa",
                    "https://www.iana.org/domains/idn-tables",
                    "https://www.iana.org/abuse",
                    "https://www.iana.org/time-zones",
                    "https://www.iana.org/news",
                    "https://www.iana.org/performance",
                    "https://www.iana.org/about/excellence",
                    "https://www.iana.org/archive",
                    "https://www.iana.org/contact",
                    "https://pti.icann.org",
                    "http://www.icann.org/",
                    "https://www.icann.org/privacy/policy",
                    "https://www.icann.org/privacy/tos",
                ],
            ),
            (
                SCRAP_HTML_DATA_FILEPATH_2,
                "https://www.iana.org/domains",
                [
                    "https://www.iana.org/",
                    "https://www.iana.org/domains",
                    "https://www.iana.org/protocols",
                    "https://www.iana.org/numbers",
                    "https://www.iana.org/about",
                    "https://www.iana.org/domains/root",
                    "https://www.iana.org/domains/int",
                    "https://www.iana.org/domains/arpa",
                    "https://www.iana.org/domains/idn-tables",
                    "https://www.iana.org/dnssec",
                    "https://www.iana.org/domains/special",
                    "https://www.iana.org/domains/root/db",
                    "https://www.iana.org/domains/root/files",
                    "https://www.iana.org/domains/root/manage",
                    "https://www.iana.org/domains/root/help",
                    "https://www.iana.org/domains/root/servers",
                    "https://www.iana.org/domains/int/manage",
                    "https://www.iana.org/domains/int/policy",
                    "https://www.iana.org/help/idn-repository-procedure",
                    "https://www.iana.org/dnssec/files",
                    "https://www.iana.org/dnssec/ceremonies",
                    "https://www.iana.org/dnssec/procedures",
                    "https://www.iana.org/dnssec/tcrs",
                    "https://www.iana.org/domains/reserved",
                    "https://www.iana.org/abuse",
                    "https://www.iana.org/time-zones",
                    "https://www.iana.org/news",
                    "https://www.iana.org/performance",
                    "https://www.iana.org/about/excellence",
                    "https://www.iana.org/archive",
                    "https://www.iana.org/contact",
                    "https://pti.icann.org",
                    "http://www.icann.org/",
                    "https://www.icann.org/privacy/policy",
                    "https://www.icann.org/privacy/tos",
                ],
            ),
        ],
    )
    def test_html_parser_links_extraction(
        self, scrap_html_data, filepath, base_url, expected_links
    ):
        """Test that HTMLParser correctly extracts links from given HTML test files."""
        html_data = scrap_html_data.get(filepath)
        extracted_links = HTMLParser(url=base_url, html=html_data).links
        assert expected_links == extracted_links, (
            f"Link extraction mismatch for {filepath}\n"
            f"Base URL: {base_url}\n"
            f"Extracted: {extracted_links}\n"
            f"Expected: {expected_links}"
        )

    def test_html_parser_markdown_extraction(self, scrap_html_data):
        """Verify that HTMLParser correctly converts scraped HTML into Markdown."""
        with open(
            MARKDOWN_PARSED_DATA_FOR_DATA_1,
            "r",
        ) as f:
            expected_markdown = f.read()
        html_data = scrap_html_data.get(SCRAP_HTML_DATA_FILEPATH_1)
        generated_markdown = HTMLParser(
            url="https://www.iana.org/help/example-domains", html=html_data
        ).markdown
        assert expected_markdown == generated_markdown

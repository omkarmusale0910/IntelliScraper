# Content Parsers

IntelliScraper provides an extensible parser hierarchy for extracting structured data from scraped HTML.

## Parser Hierarchy

```
BaseParser (ABC)
└── HTMLParser (general purpose)
    └── YourCustomParser (extend for your site)
```

## HTMLParser

The default parser for extracting text, links, and Markdown from any HTML page.

```python
from intelliscraper.parsers import HTMLParser

parser = HTMLParser(url="https://example.com", html=html_content)

# Plain text
print(parser.text)

# All absolute URLs from <a> tags
print(parser.links)

# Classified internal/external links with metadata
print(parser.navigable_links)

# Full Markdown
print(parser.markdown)

# Cleaned Markdown optimised for LLM input
print(parser.markdown_for_llm)
```

### Properties

| Property | Type | Description |
|---|---|---|
| `text` | `str` | Plain text with newline separators |
| `links` | `list[str]` | Deduplicated absolute HTTP/HTTPS URLs |
| `navigable_links` | `list[dict]` | Classified links with href, text, title, link_type, rel |
| `markdown` | `str` | Full-page Markdown (standard preprocessing) |
| `markdown_for_llm` | `str` | Cleaned Markdown (nav, ads, forms stripped) |

All properties are lazily computed and cached on first access.

## Creating Custom Parsers

Extend `HTMLParser` to add site-specific extraction logic:

```python
from functools import cached_property
from intelliscraper.parsers import HTMLParser

class ProductPageParser(HTMLParser):
    """Parser for an e-commerce product page."""

    @cached_property
    def product_title(self) -> str | None:
        tag = self.soup.select_one("h1.product-title")
        return tag.get_text(strip=True) if tag else None

    @cached_property
    def price(self) -> str | None:
        tag = self.soup.select_one("span.price")
        return tag.get_text(strip=True) if tag else None

    @cached_property
    def description(self) -> str | None:
        tag = self.soup.select_one("div.product-description")
        return tag.get_text(separator="\n", strip=True) if tag else None
```

### Usage

```python
async with AsyncScraper() as scraper:
    response = await scraper.scrape("https://shop.example.com/product/123")

    if response.status == ScrapStatus.SUCCESS:
        parser = ProductPageParser(
            url=response.scrape_request.url,
            html=response.scrap_html_content,
        )
        print(f"Title: {parser.product_title}")
        print(f"Price: {parser.price}")
```



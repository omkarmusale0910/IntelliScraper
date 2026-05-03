# IntelliScraper

A powerful **anti-bot detection async web scraping** library built on Playwright.  Designed for scraping protected sites job platforms, social networks, e-commerce dashboardsthat require authentication and sophisticated anti-detection.

[![PyPI Version](https://img.shields.io/pypi/v/intelliscraper-core)](https://pypi.org/project/intelliscraper-core/)
[![Documentation](https://img.shields.io/badge/docs-ReadTheDocs-blue)](https://intelliscraper.readthedocs.io/en/latest/)
![Python Version](https://img.shields.io/badge/python-3.12%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-active-success)

---

## 📖 Documentation

For detailed guides, tutorials, and full API reference, please visit our **[official documentation](https://intelliscraper.readthedocs.io/en/latest/)**.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🔐 **Session Management** | Capture and reuse authentication sessions (cookies, localStorage, fingerprints) |
| 🖥️ **Local Browser Mode** | Connect to your running Chrome via CDP all existing logins available instantly |
| 🤖 **Managed Browser Mode** | Launch headless Chromium with fingerprint spoofing and anti-detection |
| ⏱️ **Rate Limiting** | Token-bucket rate limiter shared across all concurrent pages |
| 📦 **Batch Scraping** | `batch_scrape()` for processing hundreds of URLs with concurrency + rate control |
| 🛡️ **Anti-Detection** | WebDriver flag removal, plugin spoofing, WebGL masking, human-like scrolling |
| 🌐 **Proxy Support** | Bright Data integration and custom proxy providers |
| 📝 **Extensible Parsers** | HTML → text, links, Markdown. Extend for site-specific parsing |
| ⚡ **Fully Async** | Built with `async`/`await` for maximum concurrency |

---

## 🚀 Quick Start

### Installation

```bash
# Install the package
pip install intelliscraper-core

# Install Playwright browser (Chromium)
playwright install chromium
```

> [!NOTE]
> Playwright requires browser binaries installed separately.  The command above installs Chromium.

---

## ⚡ Basic Scraping

```python
import asyncio
from intelliscraper import AsyncScraper, ScrapStatus

async def main():
    async with AsyncScraper() as scraper:
        response = await scraper.scrape("https://example.com")

        if response.status == ScrapStatus.SUCCESS:
            print(f"HTTP {response.http_status_code}")
            print(f"Time: {response.elapsed_time:.2f}s")
            print(response.scrap_html_content[:500])

asyncio.run(main())
```

---

## 📦 Batch Scraping with Rate Limiting

Scrape many URLs with automatic rate limiting and concurrency control:

```python
import asyncio
from intelliscraper import AsyncScraper, ScrapStatus

async def main():
    async with AsyncScraper(
        max_concurrent_pages=4,
        max_requests_per_minute=900,  # 15 requests/sec across all pages
    ) as scraper:
        urls = [f"https://example.com/page/{i}" for i in range(100)]
        results = await scraper.batch_scrape(urls)

        for result in results:
            print(
                f"{result.scrape_request.url} → "
                f"{result.status.value} "
                f"(HTTP {result.http_status_code}, "
                f"{result.elapsed_time:.2f}s)"
            )

asyncio.run(main())
```

> [!IMPORTANT]
> The rate limit is **shared across all concurrent pages**.  With `max_concurrent_pages=4` and `max_requests_per_minute=900`, the 4 pages share a combined budget of 15 requests/second not 15/sec each.

---

## 🖥️ Local Browser Mode (CDP)

Connect to your running Chrome instance to reuse existing logins (LinkedIn, Gmail, etc.).

### Setup (one-time)

```bash
# 1. Create the debug profile
make chrome-debug-profile

# 2. Open Chrome with the debug profile and log into your target sites
make chrome-debug-login URL=https://www.linkedin.com

# 3. Log in to the site in the browser that opens
# 4. Close Chrome when done
```

> [!WARNING]
> The debug profile (`~/.config/google-chrome-debug`) is **separate** from your default Chrome profile.  You must log into target sites in this profile before scraping.

### Usage

```python
import asyncio
from intelliscraper import AsyncScraper, ScrapStatus

async def main():
    async with AsyncScraper(
        use_local_browser=True,
        headless=False,
    ) as scraper:
        response = await scraper.scrape(
            "https://www.linkedin.com/jobs/collections/recommended/"
        )

        if response.status == ScrapStatus.SUCCESS:
            print(f"HTTP {response.http_status_code}")
            print(f"Session: {response.session_id}")
            print(f"Mode: {response.browser_mode}")

asyncio.run(main())
```

### How It Works

1. IntelliScraper checks if Chrome is running with `--remote-debugging-port=9222`.
2. If not, it auto-launches Chrome using the debug profile.
3. Connects via CDP and reuses the existing browser context (all cookies and logins preserved).
4. Only the pages opened by IntelliScraper are closed on exit your Chrome session stays running.

---

## 🔐 Session-Based Scraping (Managed Browser)

For sites that require authentication without using your local Chrome:

### 1. Capture a Session

```bash
intelliscraper-session \
    --url "https://example.com" \
    --site "example" \
    --output "./example_session.json"
```

This opens a browser log in, then press Enter.  Session data (cookies, localStorage, fingerprint) is saved to JSON.

### 2. Use the Session

```python
import asyncio
import json
from intelliscraper import AsyncScraper, Session, ScrapStatus

async def main():
    with open("example_session.json") as f:
        session = Session(**json.load(f))

    async with AsyncScraper(session_data=session) as scraper:
        response = await scraper.scrape("https://example.com/dashboard")

        if response.status == ScrapStatus.SUCCESS:
            print(f"Session: {response.session_id}")
            print(response.scrap_html_content[:500])

asyncio.run(main())
```

---

## 📝 HTML Parsing

### Default Parser

```python
from intelliscraper.parsers import HTMLParser

parser = HTMLParser(url="https://example.com", html=html_content)
print(parser.text)               # Plain text
print(parser.links)              # List of absolute URLs
print(parser.navigable_links)    # Classified internal/external links
print(parser.markdown)           # Full Markdown
print(parser.markdown_for_llm)   # Cleaned Markdown (for LLM input)
```

### Custom Parsers

Extend `HTMLParser` for site-specific extraction:

```python
from functools import cached_property
from intelliscraper.parsers import HTMLParser

class MyJobParser(HTMLParser):
    """Custom parser for a job listing site."""

    @cached_property
    def job_title(self) -> str | None:
        tag = self.soup.select_one("h1.job-title")
        return tag.get_text(strip=True) if tag else None

    @cached_property
    def company(self) -> str | None:
        tag = self.soup.select_one("span.company-name")
        return tag.get_text(strip=True) if tag else None
```



---

## 🌐 Proxy Support

Proxy is used in **managed browser mode only** (not with local browser / CDP).

### Bright Data Proxy

```python
import asyncio
from intelliscraper import AsyncScraper, BrightDataProxy, ScrapStatus

async def main():
    proxy = BrightDataProxy(
        host="brd.superproxy.io",
        port=22225,
        username="your-username",
        password="your-password",
    )

    async with AsyncScraper(proxy=proxy) as scraper:
        response = await scraper.scrape("https://example.com")
        print(f"Status: {response.status.value}")

asyncio.run(main())
```

### Custom Proxy Provider

```python
from intelliscraper import ProxyProvider, Proxy

class MyProxy(ProxyProvider):
    def get_proxy(self) -> Proxy:
        return Proxy(
            server="http://my-proxy.com:8080",
            username="user",
            password="pass",
        )
```

> [!NOTE]
> All pages within a single `AsyncScraper` instance share the same proxy.  For different proxies, create separate `AsyncScraper` instances.

---

## 📊 Response Model

Every `scrape()` and `batch_scrape()` call returns a `ScrapeResponse` with:

| Field | Type | Description |
|---|---|---|
| `scrape_request` | `ScrapeRequest` | Original request parameters |
| `status` | `ScrapStatus` | Outcome: `SUCCESS`, `PARTIAL_SUCCESS`, `FAILED`, `RATE_LIMITED`, `BLOCKED`, `TIMEOUT` |
| `http_status_code` | `int \| None` | Actual HTTP status from the server (200, 403, 429, etc.) |
| `elapsed_time` | `float \| None` | Total scrape duration in seconds |
| `scrap_html_content` | `str \| None` | Raw HTML from the page |
| `error_msg` | `str \| None` | Error message on failure |
| `session_id` | `str \| None` | Session `site` identifier used |
| `browser_mode` | `str \| None` | `"local_browser"` or `"managed_browser"` |

---

## 🏗️ Architecture

```
intelliscraper/
├── scraper.py              # AsyncScraper main orchestrator
├── rate_limiter.py         # Token-bucket rate limiter
├── enums.py                # ScrapStatus, BrowsingMode, HTMLParserType
├── exception.py            # Custom exceptions
├── utils.py                # URL normalisation utilities
│
├── browser/                # Browser backend strategy pattern
│   ├── backend.py          # BrowserBackend ABC
│   ├── local.py            # LocalBrowserBackend (CDP)
│   └── managed.py          # ManagedBrowserBackend (Playwright)
│
├── parsers/                # Content parsers
│   ├── base_parser.py      # BaseParser ABC
│   └── html_parser.py      # HTMLParser (general purpose)
│
├── common/
│   ├── constants.py        # Browser fingerprints, launch options
│   └── models.py           # Pydantic models (Proxy, Session, etc.)
│
├── proxy/
│   ├── base.py             # ProxyProvider ABC
│   └── brightdata.py       # BrightDataProxy
│
└── scripts/
    └── get_session_data.py # CLI session capture tool
```

---

## 📋 Requirements

* Python 3.12+
* Playwright + Chromium
* Compatible with Linux, macOS, and Windows

---

## 🛠️ Development

```bash
# Install dependencies
make install

# Install Playwright Chromium
make playwright-chromium

# Run tests
make test

# Format code
make format
```

### Chrome Debug Profile Commands

```bash
make chrome-debug-profile                        # Create debug profile
make chrome-debug-login URL=https://linkedin.com  # Log in to a site
make chrome-debug-stop                            # Stop Chrome debug
```

---

## 🗺️ Roadmap

* ✅ Async scraping with concurrent pages
* ✅ Local browser mode (CDP)
* ✅ Session management CLI
* ✅ Proxy integration (Bright Data)
* ✅ HTML parsing and Markdown generation
* ✅ Anti-detection mechanisms
* ✅ Rate limiting (token bucket)
* ✅ Batch scraping API
* ✅ Extensible parser architecture
* 🔄 Proxy rotation
* 🔄 Distributed crawler mode
* 🔄 AI-based content extraction

---

## 📄 License

Licensed under the **MIT License**.

---

## 📧 Support

For help, issues, or contributions visit the [GitHub Issues page](https://github.com/omkarmusale0910/IntelliScraper/issues).

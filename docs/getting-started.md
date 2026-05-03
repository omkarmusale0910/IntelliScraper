# Getting Started

## Installation

```bash
# Install the package
pip install intelliscraper-core

# Install Playwright browser (Chromium)
playwright install chromium
```

```{note}
Playwright requires browser binaries installed separately.  The command above installs Chromium, which is required for IntelliScraper.
```

## Basic Scraping

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

## Session-Based Scraping

For sites that require authentication:

### 1. Capture a Session

```bash
intelliscraper-session \
    --url "https://example.com" \
    --site "example" \
    --output "./example_session.json"
```

This opens a browser — log in, then press Enter.  Session data (cookies, localStorage, fingerprint) is saved to JSON.

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

```{important}
Sessions maintain internal time-series statistics (timestamps, statuses). These help analyse rate limits and performance.  Excessive concurrency may cause failures — scale gradually.
```

## Response Model

Every `scrape()` and `batch_scrape()` call returns a `ScrapeResponse`:

| Field | Type | Description |
|---|---|---|
| `scrape_request` | `ScrapeRequest` | Original request parameters |
| `status` | `ScrapStatus` | Outcome: `SUCCESS`, `PARTIAL_SUCCESS`, `FAILED`, `RATE_LIMITED`, `BLOCKED`, `TIMEOUT` |
| `http_status_code` | `int \| None` | HTTP status from the server (200, 403, 429, etc.) |
| `elapsed_time` | `float \| None` | Scrape duration in seconds |
| `scrap_html_content` | `str \| None` | Raw HTML from the page |
| `error_msg` | `str \| None` | Error message on failure |
| `session_id` | `str \| None` | Session site identifier |
| `browser_mode` | `str \| None` | `"local_browser"` or `"managed_browser"` |

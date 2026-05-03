# Batch Scraping & Rate Limiting

## Batch Scraping

Use `batch_scrape()` to scrape many URLs with automatic concurrency and rate control:

```python
import asyncio
from intelliscraper import AsyncScraper, ScrapStatus

async def main():
    async with AsyncScraper(
        max_concurrent_pages=4,
        max_requests_per_minute=900,  # 15 requests/sec
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

### How It Works

1. `batch_scrape(urls)` creates async tasks for all URLs.
2. The page-pool semaphore limits concurrency to `max_concurrent_pages`.
3. The rate limiter enforces `max_requests_per_minute` **across all pages combined**.
4. Results are returned in the same order as the input URLs.

## Rate Limiting

The rate limiter uses a **token-bucket algorithm** shared across all concurrent pages.

```{important}
The rate limit is **global** — with `max_concurrent_pages=4` and `max_requests_per_minute=900` (15/sec), all 4 pages share the same 15/sec budget, not 15/sec each.
```

### Configuration

| Parameter                   | Default             | Description                          |
| --------------------------- | ------------------- | ------------------------------------ |
| `max_requests_per_minute` | `None` (no limit) | Requests per minute across all pages |

### Examples

```python
# No rate limiting (default)
AsyncScraper()

# 15 requests per second (across all pages)
AsyncScraper(max_requests_per_minute=900)

# 1 request per second (conservative, for protected sites)
AsyncScraper(max_requests_per_minute=60)

# 1 request every 4 seconds (very conservative)
AsyncScraper(max_requests_per_minute=15)
```

### Logging

The rate limiter logs when it throttles:

```
DEBUG:intelliscraper.rate_limiter:Rate limiter: waiting 0.07s before next request (900 rpm limit)
```

Enable debug logging to see rate limiter activity:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Combining with Single Scrapes

You can mix `batch_scrape()` and `scrape()` in the same session they share the same rate limiter:

```python
async with AsyncScraper(max_requests_per_minute=900) as scraper:
    # Batch scrape 100 URLs
    results = await scraper.batch_scrape(urls[:100])

    # Then do a targeted single scrape
    detail = await scraper.scrape("https://example.com/detail/123")
```

"""Simple Example: Scraping multiple URLs with session authentication."""

import asyncio
import json

from intelliscraper import AsyncScraper, ScrapStatus, Session


async def main():
    """Scrape multiple URLs with session data and batch API."""

    urls = [
        "https://www.example.com/protected/page1",
        "https://www.example.com/protected/page2",
        "https://www.example.com/protected/page3",
        "https://www.example.com/protected/page4",
    ]

    # Load session data from JSON file.
    with open("example_session.json", "r") as f:
        session_data = json.load(f)

    session = Session(**session_data)

    # Use batch_scrape for multiple URLs with rate limiting.
    async with AsyncScraper(
        headless=False,
        session_data=session,
        max_concurrent_pages=4,
        max_requests_per_minute=900,  # 15 requests/sec
    ) as scraper:
        results = await scraper.batch_scrape(urls)

    # Process results.
    for i, result in enumerate(results, 1):
        if result.status in (ScrapStatus.SUCCESS, ScrapStatus.PARTIAL_SUCCESS):
            print(
                f"✓ URL {i}: {result.status.value} "
                f"(HTTP {result.http_status_code}, "
                f"{len(result.scrap_html_content)} bytes, "
                f"{result.elapsed_time:.2f}s)"
            )
            with open(f"output_{i}.html", "w", encoding="utf-8") as f:
                f.write(result.scrap_html_content)
        else:
            print(f"URL {i}: {result.status.value} — {result.error_msg}")


if __name__ == "__main__":
    asyncio.run(main())

"""Temporary script to test batch scraping LinkedIn with the local browser.

INSTRUCTIONS:
1. Make sure your local debug Chrome is running and you are logged into LinkedIn:
   make chrome-debug-login URL=https://www.linkedin.com

2. Keep that Chrome window OPEN (don't close it!).

3. Add your desired LinkedIn URLs to the `urls` list below.

4. Run this script in your terminal:
   uv run tmp.py
"""

import asyncio
import logging

from intelliscraper import AsyncScraper, BrowsingMode, ScrapStatus
from intelliscraper.parsers import HTMLParser

# Enable logging to see the rate limiter and scraper in action
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


async def main():
    # Replace these with your actual LinkedIn URLs.
    # Here are some sample job URLs:
    urls = [
        "https://github.com/omkarmusale0910",
        "https://www.linkedin.com/in/omkar-musale-dev/",
        "https://medium.com/@omkarmusaleich",
        "https://pypi.org/project/intelliscraper-core/",
    ]

    print(f"Starting batch scrape of {len(urls)} LinkedIn URLs...")

    # Initialize AsyncScraper with local browser mode
    async with AsyncScraper(
        headless=False,
        use_local_browser=True,  # Connect to the Chrome window you just opened
        max_concurrent_pages=2,  # Scrape 2 tabs at the same time (keep it low for LinkedIn)
        max_requests_per_minute=15,  # Strict Rate limit: 15 requests per minute (1 every 4 seconds)
        browsing_mode=BrowsingMode.HUMAN_LIKE,  # Adds human-like scrolling to avoid bot detection
    ) as scraper:

        # Batch scrape! The rate limiter will ensure it stays under 15/min automatically.
        results = await scraper.batch_scrape(urls)

    print("\n" + "=" * 50)
    print("=== SCRAPING RESULTS ===")
    print("=" * 50 + "\n")

    for i, result in enumerate(results, 1):
        url = result.scrape_request.url
        status = result.status.value

        if result.status in (ScrapStatus.SUCCESS, ScrapStatus.PARTIAL_SUCCESS):
            # We can use our custom HTML parser here!
            parser = HTMLParser(url=url, html=result.scrap_html_content)

            print(f"✓ [{status}] (HTTP {result.http_status_code}) - {url}")
            print(f"  └─ markdown_for_llm:       {parser.markdown_for_llm[:20]}")
            print(f"  └─ Time taken:  {result.elapsed_time:.2f}s")
            print("-" * 50)

        else:
            print(f"✗ [{status}] (HTTP {result.http_status_code}) - {url}")
            if result.error_msg:
                print(f"  └─ Error: {result.error_msg}")
            print("-" * 50)


if __name__ == "__main__":
    asyncio.run(main())

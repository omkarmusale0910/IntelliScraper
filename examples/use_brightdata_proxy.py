"""
Example: Using Bright Data Proxy with IntelliScraper (Async Version)

Use a proxy with this web scraper, utilizing asynchronous blocks.

This example demonstrates how to use the `BrightDataProxy` class from the
`intelliscraper.proxy.brightdata` module together with the `AsyncScraper` class
from `intelliscraper.scraper` to scrape a web page through a Bright Data
(residential) proxy network asynchronously.

Usage:
    uv run examples/use_brightdata_proxy.py

### Prerequisites
- Bright Data account and a valid proxy zone configuration.
  - For proxy creation and configuration, follow https://brightdata.com/cp/zones/new
"""

import asyncio
import logging
import os
from datetime import timedelta

from intelliscraper import AsyncScraper, BrightDataProxy, HTMLParser, ScrapStatus

logging.basicConfig(level=logging.INFO)


async def main():
    # Load Bright Data credentials from environment variables for security.
    host = os.getenv("BRIGHTDATA_HOST", "")
    username = os.getenv("BRIGHTDATA_USERNAME", "")
    password = os.getenv("BRIGHTDATA_PASSWORD", "")
    port = int(os.getenv("BRIGHTDATA_PORT", "33335"))

    if not all((host, username, password)):
        logging.error(
            "Missing Bright Data credentials. Please set BRIGHTDATA_HOST, "
            "BRIGHTDATA_USERNAME, and BRIGHTDATA_PASSWORD environment variables."
        )
        return

    # Create Bright Data proxy instance
    bright_data_proxy = BrightDataProxy(
        host=host,
        port=port,
        username=username,
        password=password,
    )

    # Use AsyncScraper with a context manager for proper cleanup
    async with AsyncScraper(headless=True, proxy=bright_data_proxy) as scraper:
        scrape_response = await scraper.scrape(
            url="https://www.iana.org/help/example-domains",
            timeout=timedelta(seconds=30),
        )

        if scrape_response.status != ScrapStatus.FAILED:
            html_parser = HTMLParser(
                url=scrape_response.scrape_request.url,
                html=scrape_response.scrap_html_content,
            )

            logging.info("Scraped content using Bright Data proxy:")
            logging.info(html_parser.markdown)

            logging.info("Scraped links using Bright Data proxy:")
            logging.info(html_parser.links)
        else:
            logging.error(
                f"Scrape failed for URL: {scrape_response.scrape_request.url}"
            )


if __name__ == "__main__":
    asyncio.run(main())

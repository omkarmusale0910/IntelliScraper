"""Example: Using Bright Data Proxy with IntelliScraper.

Demonstrates using ``BrightDataProxy`` with ``AsyncScraper`` to scrape
through Bright Data's residential proxy network.

Prerequisites:
    - Bright Data account and a valid proxy zone.
    - Set environment variables: BRIGHTDATA_HOST, BRIGHTDATA_USERNAME,
      BRIGHTDATA_PASSWORD, BRIGHTDATA_PORT.

Usage:
    uv run examples/use_brightdata_proxy.py
"""

import asyncio
import logging
import os
from datetime import timedelta

from intelliscraper import AsyncScraper, BrightDataProxy, ScrapStatus
from intelliscraper.parsers import HTMLParser

logging.basicConfig(level=logging.INFO)


async def main():
    # Load credentials from environment variables.
    host = os.getenv("BRIGHTDATA_HOST", "")
    username = os.getenv("BRIGHTDATA_USERNAME", "")
    password = os.getenv("BRIGHTDATA_PASSWORD", "")
    port = int(os.getenv("BRIGHTDATA_PORT", "33335"))

    if not all((host, username, password)):
        logging.error(
            "Missing Bright Data credentials.  Set BRIGHTDATA_HOST, "
            "BRIGHTDATA_USERNAME, and BRIGHTDATA_PASSWORD."
        )
        return

    bright_data_proxy = BrightDataProxy(
        host=host,
        port=port,
        username=username,
        password=password,
    )

    async with AsyncScraper(headless=True, proxy=bright_data_proxy) as scraper:
        response = await scraper.scrape(
            url="https://www.iana.org/help/example-domains",
            timeout=timedelta(seconds=30),
        )

        if response.status != ScrapStatus.FAILED:
            parser = HTMLParser(
                url=response.scrape_request.url,
                html=response.scrap_html_content,
            )
            logging.info("HTTP status: %s", response.http_status_code)
            logging.info("Browser mode: %s", response.browser_mode)
            logging.info("Markdown:\n%s", parser.markdown)
            logging.info("Links: %s", parser.links)
        else:
            logging.error(
                "Scrape failed: %s — %s",
                response.scrape_request.url,
                response.error_msg,
            )


if __name__ == "__main__":
    asyncio.run(main())

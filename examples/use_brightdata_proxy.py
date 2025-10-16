"""
Example: Using Bright Data Proxy with IntelliScraper

This example demonstrates how to use the `BrightDataProxy` class from the
`intelliscraper.proxy.brightdata` module together with the `Scraper` class
from `intelliscraper.scraper` to scrape a web page through a Bright Data
(residential) proxy network.

Usage:
    uv run examples/use_brightdata_proxy.py

### Prerequisites
- Bright Data account and a valid proxy zone configuration.
  - for proxy creation and configuration follow https://brightdata.com/cp/zones/new
"""

import logging
import os
from datetime import timedelta

from intelliscraper import BrightDataProxy, HTMLParser, Scraper, ScrapStatus

logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    # Set up a Bright Data account, create and configure a proxy,
    # and add the configuration values here.

    # The configuration values are loaded from environment variables for security.
    host = os.getenv("BRIGHTDATA_HOST", default="")
    username = os.getenv("BRIGHTDATA_USERNAME", default="")
    password = os.getenv("BRIGHTDATA_PASSWORD", default="")

    if not all((host, username, password)):
        logging.error(
            "Missing Bright Data credentials. Please set BRIGHTDATA_HOST, "
            "BRIGHTDATA_USERNAME, and BRIGHTDATA_PASSWORD environment variables."
        )
        exit(1)

    bright_data_proxy = BrightDataProxy(
        host=host,
        port=int(os.getenv("BRIGHTDATA_PORT", "33335")),
        username=username,
        password=password,
    )
    web_scraper_with_proxy = Scraper(headless=True, proxy=bright_data_proxy)
    scrape_response = web_scraper_with_proxy.scrape(
        url="https://www.iana.org/help/example-domains", timeout=timedelta(seconds=30)
    )
    if scrape_response.status != ScrapStatus.FAILED:
        html_parser = HTMLParser(
            url=scrape_response.scrape_request.url,
            html=scrape_response.scrap_html_content,
        )
        logging.info("Scrap content using bright data proxy")
        logging.info(html_parser.markdown)
        logging.info("Scrap links using bright data proxy")
        logging.info(html_parser.links)
    else:
        logging.error(f"Scrape failed for URL: {scrape_response.scrape_request.url}")

"""
Example: Using Bright Data Proxy with IntelliScraper

This example demonstrates how to use the `BrightDataProxy` class from the
`intelliscraper.proxy.brightdata` module together with the `Scraper` class
from `intelliscraper.scraper` to scrape a web page through a Bright Data
(residential) proxy network.

Usage:
    uv run intelliscraper/examples/use_brightdata_proxy.py

### Prerequisites
- Bright Data account and a valid proxy zone configuration.
  - for proxy creation and configuration follow https://brightdata.com/cp/zones/new
"""

import logging
from datetime import timedelta
from pprint import pprint

from intelliscraper.proxy.brightdata import BrightDataProxy
from intelliscraper.scraper import Scraper

logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    # Set up a Bright Data account, create and configure a proxy,
    # and add the configuration values here.
    bright_data_proxy = BrightDataProxy(
        host="",
        port=33335,
        username="",
        password="",
    )
    web_scarper_with_proxy = Scraper(headless=True, proxy=bright_data_proxy)
    html_parser = web_scarper_with_proxy.scrap(
        url="https://www.iana.org/help/example-domains", timeout=timedelta(seconds=30)
    )
    logging.info("Scrap content using brigh data proxy")
    logging.info(html_parser.markdown)
    logging.info("Scrap links using brigh data proxy")
    logging.info(html_parser.links)

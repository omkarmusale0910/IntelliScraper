import logging
from datetime import timedelta

from playwright.sync_api import TimeoutError, sync_playwright

from intelliscraper.exception import ScrapError


class Scraper:
    """A web scraper that retrieves HTML content from a given URL."""

    # Single context for all scraping (OPTIMAL)
    CONTEXT_OPTIONS = {
        "viewport": {"width": 1920, "height": 1080},
        "user_agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
        "ignore_https_errors": True,  # Handle SSL errors
    }

    def __init__(
        self,
        headless: bool = True,
        context_options: dict = CONTEXT_OPTIONS,
        proxy: dict = None,
        open_new_page_per_scrape: bool = False,
    ):
        """Initialize the scraper.

        Args:
            headless (bool): Run browser without UI (if applicable).
            context_options (dict): Optional settings for browser context.
            proxy (dict, optional): Proxy configuration.
            open_new_page_per_scrape (bool): If True, open a new page for each scrape.
        """
        self.playwright = sync_playwright().start()
        self.context_options = context_options
        self.open_new_page_per_scrape = open_new_page_per_scrape
        # Browser launch options
        launch_options = {
            "headless": headless,
            "args": [
                "--disable-blink-features=AutomationControlled",  # Stealth mode
                "--disable-dev-shm-usage",
                "--no-sandbox",
            ],
        }

        self.browser = self.playwright.chromium.launch(**launch_options)

        if proxy:
            self.context_options["proxy"] = proxy

        self.context = self.browser.new_context(**context_options)
        self.page = None

    def __del__(self):
        """Cleanup on destruction."""
        try:
            self.context.close()
            self.browser.close()
            self.playwright.stop()
            logging.debug("Cleanup complete")
        except:
            pass

    def _get_page(self):
        """Return a page instance, creating a new one if needed."""
        if self.page is None:
            self.page = self.context.new_page()

        if self.open_new_page_per_scrape:
            return self.context.new_page()

        return self.page

    def scrap(self, url: str, timeout: timedelta = timedelta(seconds=30)):
        """Navigate to the given URL and return the page content.

        Args:
            url (str): The target URL to scrape.
            timeout (timedelta, optional): Maximum wait time for page load.
                                           Defaults to 30 seconds.

        Returns:
            str: The HTML content of the page, even if a timeout occurs.

        Raises:
            ScrapError: If scraping fails due to an unexpected error.
        """
        page = self._get_page()
        try:
            page.goto(
                url=url,
                wait_until="networkidle",
                timeout=timeout.total_seconds() * 1000,
            )
            return page.content()
        except TimeoutError:
            logging.warning(
                f"Timeout while loading URL: {url}. "
                f"Waited {timeout.total_seconds()} seconds. Returning partial content."
            )
            return page.content()
        except Exception as e:
            logging.error(f"Failed to scrape data for URL: {url}. Error: {e}")
            raise ScrapError(f"Scraping failed for URL: {url}") from e

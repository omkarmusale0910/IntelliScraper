from datetime import timedelta

from pydantic import BaseModel, Field

from intelliscraper.enums import BrowsingMode, ScrapStatus


class Session(BaseModel):
    """Browser session data model."""

    site: str = Field(description="The name or identifier of the target site.")
    base_url: str = Field(description="The base URL used for scraping or crawling.")
    cookies: list[dict] = Field(
        description="List of cookies captured from the session."
    )
    localStorage: dict | None = Field(
        default=None,
        description="Key-value pairs from browser's localStorage, if available.",
    )
    sessionStorage: dict | None = Field(
        default=None,
        description="Key-value pairs from browser's sessionStorage, if available.",
    )
    fingerprint: dict = Field(
        default_factory=dict,
        description="Browser fingerprint data for session identification.",
    )


class Proxy(BaseModel):
    """Proxy configuration used for network requests."""

    server: str = Field(
        (
            "Proxy server URL or host:port. "
            "Supports HTTP and SOCKS schemes (e.g. "
            "`http://myproxy.com:3128`, `socks5://myproxy.com:1080`). "
            "Short form `myproxy.com:3128` is treated as HTTP."
        ),
    )
    bypass: str | None = Field(
        default=None,
        description=(
            "Comma-separated list of domains to bypass the proxy. "
            "Use leading dot for subdomain patterns (e.g. `.example.com,localhost`)."
        ),
    )
    username: str | None = Field(
        default=None, description="Username for proxy authentication, if required."
    )
    password: str | None = Field(
        default=None, description="Password for proxy authentication, if required."
    )


class ScrapeRequest(BaseModel):
    """Represents the input configuration for a single scraping request.

    This model defines all parameters required before initiating a scrape,
    including the target URL, timeout, browser settings, proxy, and session data.
    """

    url: str = Field(description="The target URL that was scraped.")
    timeout: timedelta = Field(
        description="Maximum time allowed for the page to load before timing out."
    )
    browser_launch_options: dict | None = Field(
        default=None,
        description="Options used to launch the browser (e.g., headless mode, useragent, etc.).",
    )
    proxy: Proxy | None = Field(
        default=None,
        description="Proxy configuration details used during the scrape, if any.",
    )
    session_data: Session | None = Field(
        default=None,
        description="Session information such as cookies, storage state, and authentication data.",
    )
    browsing_mode: BrowsingMode | None = Field(
        default=None,
        description="Defines how the browser behaves during scraping (e.g., human-like or fast mode).",
    )


class ScrapeResponse(BaseModel):
    """Represents the outcome of a web scraping operation, including
    the result content, metadata, and environment details.
    """

    scrape_request: ScrapeRequest = Field(
        description="The original request object containing all scraping parameters."
    )
    status: ScrapStatus = Field(
        description="Indicates the final status of the scrape, such as completed, partial, or failed."
    )
    scrap_html_content: str | None = Field(
        default=None,
        description="The raw HTML content extracted from the target web page.",
    )
    error_msg: str | None = Field(
        default=None,
        description="Error message if scraping fails; None when successful.",
    )

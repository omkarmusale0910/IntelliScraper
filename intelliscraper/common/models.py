from collections import Counter
from datetime import timedelta
from threading import Lock

from pydantic import BaseModel, Field, PrivateAttr

from intelliscraper.enums import BrowsingMode, ScrapStatus


class RequestEvent(BaseModel):
    """Represents a single scraping request event in time-series format.

    Each event captures when a request was made and its outcome status,
    enabling detailed audit trails and performance analysis.
    """

    sent_at: float = Field(description="Unix timestamp when this request was sent")
    request_status: ScrapStatus = Field(
        description="Outcome status of the scraping request: success, partial success, or failed"
    )


class SessionStats(BaseModel):
    """
    Thread-safe statistics collector for scraping sessions.

    Maintains a time-series log of all request events and provides
    computed statistics about success rates, failures, and performance.
    All operations are thread-safe for use in multi-threaded scraping.

    Attributes:
        request_events: Chronological list of all scraping request events
    """

    # Configure Pydantic to allow Lock type
    model_config = {"arbitrary_types_allowed": True}

    request_events: list[RequestEvent] = Field(
        default_factory=list,
        description="Chronological list of all request events in this session",
    )

    # Use PrivateAttr for the lock (Pydantic v2 way)
    _lock: Lock = PrivateAttr(default_factory=Lock)

    def add_request_event(self, request_event: RequestEvent) -> None:
        """
        Add a new request event to the time-series log in a thread-safe manner.

        Args:
            request_event: The RequestEvent to record

        Thread-safe: Yes, uses internal lock to prevent race conditions
        """

        with self._lock:
            self.request_events.append(request_event)

    @property
    def stats(self) -> dict[str, int]:
        """
        Get breakdown of all request statuses.

        Returns:
            Dictionary mapping status names to their counts:
            {
                "success": int,
                "partial": int,
                "failed": int
            }

        Thread-safe: Yes
        """

        with self._lock:
            # Use Counter for efficient counting
            status_counts = Counter(
                event.request_status.value for event in self.request_events
            )

            # Ensure all statuses are present (default to 0)
            return {
                ScrapStatus.SUCCESS.value: status_counts.get(
                    ScrapStatus.SUCCESS.value, 0
                ),
                ScrapStatus.PARTIAL_SUCCESS.value: status_counts.get(
                    ScrapStatus.PARTIAL_SUCCESS.value, 0
                ),
                ScrapStatus.FAILED.value: status_counts.get(
                    ScrapStatus.FAILED.value, 0
                ),
            }


class Session(BaseModel):
    """Browser session data model."""

    site: str = Field(
        description="Identifier of the target site (e.g., 'linkedin'); used to distinguish sessions for different websites."
    )
    base_url: str = Field(description="The base URL used for scraping or crawling.")
    cookies: list[dict] = Field(
        default_factory=list,  # Better than empty list as default
        description="List of cookies captured from the session.",
    )
    localStorage: dict | None = Field(
        default=None,
        description="Key-value pairs from browser's localStorage, if available.",
    )
    sessionStorage: dict | None = Field(
        default=None,
        description="Key-value pairs from browser's sessionStorage, if available.",
    )
    fingerprint: dict | None = Field(
        default=None,
        description="Browser fingerprint data for session identification.",
    )
    # Time-series statistics
    stats: SessionStats = Field(
        default_factory=SessionStats,
        description="Time-series event log and computed statistics",
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
    elapsed_time: float | None = Field(
        default=None,
        description="Total time taken to complete the scrape operation, in seconds.",
    )
    scrap_html_content: str | None = Field(
        default=None,
        description="The raw HTML content extracted from the target web page.",
    )
    error_msg: str | None = Field(
        default=None,
        description="Error message if scraping fails; None when successful.",
    )

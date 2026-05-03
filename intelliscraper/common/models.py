"""Pydantic data models for IntelliScraper.

Defines the core data structures used throughout the library:

- ``RequestEvent`` / ``SessionStats`` — time-series request tracking.
- ``Session`` — browser session with cookies, storage, and fingerprint.
- ``Proxy`` — proxy server configuration.
- ``ScrapeRequest`` — input parameters for a scrape operation.
- ``ScrapeResponse`` — output of a scrape operation with enriched
  metadata.
"""

from __future__ import annotations

from collections import Counter
from datetime import timedelta
from threading import Lock

from pydantic import BaseModel, Field, PrivateAttr

from intelliscraper.enums import BrowsingMode, ScrapStatus


class RequestEvent(BaseModel):
    """A single scraping request event in time-series format.

    Each event captures when a request was made and its outcome,
    enabling audit trails and performance analysis.

    Attributes:
        sent_at: Unix timestamp when this request was sent.
        request_status: Outcome status of the scraping request.
    """

    sent_at: float = Field(description="Unix timestamp when this request was sent")
    request_status: ScrapStatus = Field(
        description="Outcome status of the scraping request"
    )


class SessionStats(BaseModel):
    """Thread-safe statistics collector for scraping sessions.

    Maintains a time-series log of all request events and provides
    computed statistics about success rates, failures, and performance.
    All operations are thread-safe via an internal ``Lock``.

    Attributes:
        request_events: Chronological list of all request events.
    """

    model_config = {"arbitrary_types_allowed": True}

    request_events: list[RequestEvent] = Field(
        default_factory=list,
        description="Chronological list of all request events",
    )

    _lock: Lock = PrivateAttr(default_factory=Lock)

    def add_request_event(self, request_event: RequestEvent) -> None:
        """Add a request event to the log in a thread-safe manner.

        Args:
            request_event: The ``RequestEvent`` to record.
        """
        with self._lock:
            self.request_events.append(request_event)

    @property
    def stats(self) -> dict[str, int]:
        """Get a breakdown of all request statuses.

        Returns:
            Dictionary mapping status names to counts, e.g.::

                {"success": 42, "partial_success": 3, "failed": 1, ...}
        """
        with self._lock:
            status_counts = Counter(
                event.request_status.value for event in self.request_events
            )
            return {
                status.value: status_counts.get(status.value, 0)
                for status in ScrapStatus
            }


class Session(BaseModel):
    """Browser session data for authenticated scraping.

    Captures all state needed to resume an authenticated browser
    session: cookies, localStorage, sessionStorage, and a browser
    fingerprint for anti-detection.

    Attributes:
        site: Identifier for the target site (e.g. ``"linkedin"``).
        base_url: The base URL used for scraping.
        cookies: List of cookie dicts captured from the session.
        localStorage: Key-value pairs from the browser's localStorage.
        sessionStorage: Key-value pairs from the browser's
            sessionStorage.
        fingerprint: Browser fingerprint data for anti-detection.
        stats: Time-series event log and computed statistics.
    """

    site: str = Field(description="Identifier of the target site (e.g. 'linkedin')")
    base_url: str = Field(description="The base URL used for scraping")
    cookies: list[dict] = Field(
        default_factory=list,
        description="List of cookies captured from the session",
    )
    localStorage: dict | None = Field(
        default=None,
        description="Key-value pairs from browser's localStorage",
    )
    sessionStorage: dict | None = Field(
        default=None,
        description="Key-value pairs from browser's sessionStorage",
    )
    fingerprint: dict | None = Field(
        default=None,
        description="Browser fingerprint data for anti-detection",
    )
    stats: SessionStats = Field(
        default_factory=SessionStats,
        description="Time-series event log and computed statistics",
    )


class Proxy(BaseModel):
    """Proxy configuration for network requests.

    Applied at the browser-context level in **managed browser mode
    only**.  All pages within a scraper instance share the same proxy.

    Not used in local browser mode — the user's Chrome instance
    manages its own network configuration.

    Attributes:
        server: Proxy server URL (e.g.
            ``http://myproxy.com:3128``).
        bypass: Comma-separated domains to bypass the proxy.
        username: Proxy authentication username.
        password: Proxy authentication password.
    """

    server: str = Field(
        description=(
            "Proxy server URL or host:port.  Supports HTTP and SOCKS "
            "schemes (e.g. 'http://myproxy.com:3128', "
            "'socks5://myproxy.com:1080')."
        ),
    )
    bypass: str | None = Field(
        default=None,
        description=(
            "Comma-separated domains to bypass the proxy "
            "(e.g. '.example.com,localhost')."
        ),
    )
    username: str | None = Field(
        default=None,
        description="Username for proxy authentication",
    )
    password: str | None = Field(
        default=None,
        description="Password for proxy authentication",
    )


class ScrapeRequest(BaseModel):
    """Input configuration for a single scraping request.

    Captures all parameters used to initiate a scrape, enabling
    full traceability from request to response.

    Attributes:
        url: The target URL to scrape.
        timeout: Maximum time allowed for page load.
        browser_launch_options: Options used to launch the browser.
        proxy: Proxy configuration used, if any.
        session_data: Session information used, if any.
        browsing_mode: Browser behaviour mode (FAST or HUMAN_LIKE).
    """

    url: str = Field(description="The target URL to scrape")
    timeout: timedelta = Field(description="Maximum time allowed for page load")
    browser_launch_options: dict | None = Field(
        default=None,
        description="Options used to launch the browser",
    )
    proxy: Proxy | None = Field(
        default=None,
        description="Proxy configuration used during the scrape",
    )
    session_data: Session | None = Field(
        default=None,
        description="Session information (cookies, storage, auth data)",
    )
    browsing_mode: BrowsingMode | None = Field(
        default=None,
        description="Browser behaviour mode (FAST or HUMAN_LIKE)",
    )


class ScrapeResponse(BaseModel):
    """Output of a web scraping operation with enriched metadata.

    Contains the scraped content, timing information, HTTP status,
    and metadata about which session and browser mode were used.

    Attributes:
        scrape_request: The original request parameters.
        status: Final outcome status of the scrape.
        http_status_code: Actual HTTP status code returned by the
            server (e.g. 200, 403, 429).  ``None`` if the request
            failed before receiving a response.
        elapsed_time: Total scrape duration in seconds.
        scrap_html_content: Raw HTML content from the page.
        error_msg: Error message if the scrape failed.
        session_id: Identifier of the session used (the ``site``
            field from ``Session``), or ``None`` if no session.
        browser_mode: Which browser backend was used:
            ``"local_browser"`` or ``"managed_browser"``.
    """

    scrape_request: ScrapeRequest = Field(description="The original request parameters")
    status: ScrapStatus = Field(description="Final outcome status of the scrape")
    http_status_code: int | None = Field(
        default=None,
        description="HTTP status code from the server (e.g. 200, 403, 429)",
    )
    elapsed_time: float | None = Field(
        default=None,
        description="Total scrape duration in seconds",
    )
    scrap_html_content: str | None = Field(
        default=None,
        description="Raw HTML content from the target page",
    )
    error_msg: str | None = Field(
        default=None,
        description="Error message if scraping failed; None on success",
    )
    session_id: str | None = Field(
        default=None,
        description="Session site identifier used for this scrape",
    )
    browser_mode: str | None = Field(
        default=None,
        description="Browser backend: 'local_browser' or 'managed_browser'",
    )

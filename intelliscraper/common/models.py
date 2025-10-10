from pydantic import BaseModel, Field


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

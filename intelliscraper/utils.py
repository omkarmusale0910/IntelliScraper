from urllib.parse import urldefrag, urljoin, urlparse


def normalize_links(links: list[str], base_url: str | None = None) -> list[str]:
    """
    Convert relative links to absolute URLs, remove fragments, remove duplicates.
    If base_url is None, only absolute URLs are kept.
    """
    normalized = [
        urldefrag(urljoin(base_url, link) if base_url else link)[0]
        for link in links
        if base_url or urlparse(link).scheme in ("http", "https")
    ]
    # Keep only HTTP/HTTPS URLs
    normalized = [
        link for link in normalized if urlparse(link).scheme in ("http", "https")
    ]

    return list(dict.fromkeys(normalized))

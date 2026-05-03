"""Custom exceptions for IntelliScraper."""


class HTMLParserInputError(ValueError):
    """Raised when the input provided to ``HTMLParser`` is invalid.

    Typically occurs when ``html`` is ``None``, empty, or not a string.
    """


class LocalBrowserConnectionError(Exception):
    """Raised when unable to connect to a local browser via CDP.

    This can happen when:

    - Chrome is not running with ``--remote-debugging-port=9222``.
    - The debug profile is locked by another Chrome instance.
    - The CDP endpoint is unreachable after the timeout period.
    """


class ScraperNotInitializedError(RuntimeError):
    """Raised when scraper methods are called before initialisation.

    Ensure you call ``await scraper.initialize()`` or use the async
    context manager (``async with AsyncScraper() as scraper:``) before
    calling ``scrape()`` or ``batch_scrape()``.
    """


class RateLimitExceededError(Exception):
    """Raised when a server responds with HTTP 429 Too Many Requests.

    This indicates the target site has detected too many requests
    from this client.  Consider reducing ``max_requests_per_minute``
    or adding delays between batches.
    """


class BotDetectionError(Exception):
    """Raised when bot detection is triggered by the target site.

    This typically manifests as HTTP 403 responses combined with
    CAPTCHA pages or JavaScript challenges.  Consider using session
    data with the local browser backend for authenticated access.
    """

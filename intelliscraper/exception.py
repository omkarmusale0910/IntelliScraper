class ScrapError(Exception):
    """Custom exception raised when scraping a URL fails."""

    pass


class HTMLParserInputError(ValueError):
    """Raised when the input provided to HTMLParser is invalid."""

    pass

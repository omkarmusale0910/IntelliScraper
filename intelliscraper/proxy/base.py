from abc import ABC, abstractmethod

from intelliscraper.common.models import Proxy


class ProxyProvider(ABC):
    """Abstract base class for proxy providers.

    All proxy provider implementations must inherit from this class and
    implement the get_proxy() method to return a Playwright-compatible Proxy instance.
    """

    @abstractmethod
    def get_proxy(self) -> Proxy:
        """Return a Proxy instance compatible with Playwright.

        Returns:
            Proxy: Configured proxy instance ready for use with Playwright.
        """
        pass

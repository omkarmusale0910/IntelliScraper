"""Abstract base class for proxy providers.

All proxy provider implementations must inherit from ``ProxyProvider``
and implement ``get_proxy()`` to return a Playwright-compatible
``Proxy`` instance.

Proxy is applied at the **browser-context level** in **managed browser
mode only**.  It is **not** used in local browser mode — your Chrome
instance manages its own network configuration.

All pages within a single ``AsyncScraper`` instance share the same
proxy.  For different proxies, create separate ``AsyncScraper``
instances.

Supported providers:
    - ``BrightDataProxy``: Bright Data residential/datacenter proxies.
    - Custom: Extend this class and implement ``get_proxy()``.

Example::

    class MyProxyProvider(ProxyProvider):
        def get_proxy(self) -> Proxy:
            return Proxy(
                server="http://my-proxy.com:8080",
                username="user",
                password="pass",
            )
"""

from abc import ABC, abstractmethod

from intelliscraper.common.models import Proxy


class ProxyProvider(ABC):
    """Abstract base class for proxy providers.

    Implement ``get_proxy()`` to return a ``Proxy`` instance that
    Playwright can use for network requests.

    Note:
        Proxy is only used in managed browser mode.  In local browser
        mode (CDP), the user's Chrome instance manages its own network
        settings — the proxy parameter is ignored.
    """

    @abstractmethod
    def get_proxy(self) -> Proxy:
        """Return a ``Proxy`` instance compatible with Playwright.

        Returns:
            A configured ``Proxy`` ready for use with Playwright's
            browser context.
        """

from intelliscraper.common.models import Proxy
from intelliscraper.proxy.base import ProxyProvider


class BrightDataProxy(ProxyProvider):
    """Bright Data proxy provider for residential and data center proxies."""

    def __init__(self, host: str, port: int, username: str, password: str):
        """Initialize Bright Data proxy configuration.

        Args:
            host: Bright Data proxy host (e.g., 'brd.superproxy.io').
            port: Proxy port number (e.g., 22225).
            username: Your Bright Data username with zone configuration.
            password: Your Bright Data password.
        """
        self.host = host
        self.port = port
        self.username = username
        self.password = password

    def get_proxy(self) -> Proxy:
        """Return configured Bright Data proxy instance.

        Returns:
            Proxy: Configured proxy ready for use with Playwright.
        """
        return Proxy(
            server=f"http://{self.host}:{self.port}",
            username=self.username,
            password=self.password,
        )

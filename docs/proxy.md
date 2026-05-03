# Proxy Support

Proxy support is available in **managed browser mode only**.  It is not used in local browser mode (CDP), where your Chrome instance manages its own network.

## How Proxy Works

- Proxy is applied at the **browser context level** all pages share the same proxy.
- For different proxies, create separate `AsyncScraper` instances.

## Bright Data Proxy

```python
import asyncio
from intelliscraper import AsyncScraper, BrightDataProxy, ScrapStatus

async def main():
    proxy = BrightDataProxy(
        host="brd.superproxy.io",
        port=22225,
        username="your-username",
        password="your-password",
    )

    async with AsyncScraper(proxy=proxy) as scraper:
        response = await scraper.scrape("https://example.com")
        print(f"Status: {response.status.value}")
        print(f"HTTP: {response.http_status_code}")

asyncio.run(main())
```

## Custom Proxy Provider

Extend `ProxyProvider` for your own proxy service:

```python
from intelliscraper import ProxyProvider, Proxy

class MyProxyProvider(ProxyProvider):
    def get_proxy(self) -> Proxy:
        return Proxy(
            server="http://my-proxy.com:8080",
            username="user",
            password="pass",
        )
```

## Direct Proxy

Use a `Proxy` object directly:

```python
from intelliscraper import AsyncScraper, Proxy

proxy = Proxy(
    server="http://my-proxy.com:8080",
    username="user",
    password="pass",
)

async with AsyncScraper(proxy=proxy) as scraper:
    response = await scraper.scrape("https://example.com")
```

## When to Use Proxy

| Mode                      | Proxy Used? | Notes                            |
| ------------------------- | ----------- | -------------------------------- |
| Managed browser (default) | ✅ Yes      | Applied at context level         |
| Managed browser + session | ✅ Yes      | Proxy + session cookies combined |
| Local browser (CDP)       | ❌ No       | Chrome manages its own network   |

```{note}
All pages within a single `AsyncScraper` share the same proxy.  For proxy rotation between requests, create multiple `AsyncScraper` instances with different proxies.
```

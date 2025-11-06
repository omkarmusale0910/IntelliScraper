# IntelliScraper

A powerful, **anti-bot detection asynchronous web scraping** solution built with Playwright, designed for scraping protected sites such as **job hiring platforms, social networks, e-commerce dashboards**, and other web applications that require authentication.
It features **asynchronous session management**, **proxy integration**, and **advanced HTML parsing capabilities** for high-performance and reliable scraping under **anti-bot protection** systems.

![Python Version](https://img.shields.io/badge/python-3.12%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-active-success)

---

## ✨ Features

* **🔐 Session Management** — Capture and reuse authentication sessions with cookies, local storage, and browser fingerprints.
* **🛡️ Anti-Detection** — Advanced techniques to prevent bot detection.
* **🌐 Proxy Support** — Integrated Bright Data and custom proxy configurations.
* **📝 HTML Parsing** — Extract text, links, and convert to Markdown (including LLM-optimized output).
* **🎯 CLI Tool** — Generate sessions through an interactive login flow.
* **⚡ Fully Asynchronous** — Built with async/await for maximum concurrency and non-blocking I/O.
* **🚀 Playwright-Powered** — Reliable automation framework for browser-based scraping.

---

## 🚀 Quick Start

### Installation

```bash
# Install the package
pip install intelliscraper-core

# Install Playwright browser (Chromium)
playwright install chromium
```

> [!NOTE]
> Playwright requires browser binaries to be installed separately.
> The command above installs Chromium, which is necessary for IntelliScraper to function.

> For more reference: [https://pypi.org/project/intelliscraper-core/](https://pypi.org/project/intelliscraper-core/)

---

## ⚡ Basic Asynchronous Scraping (No Authentication)

```python
import asyncio
from intelliscraper import AsyncScraper, ScrapStatus

async def main():
    async with AsyncScraper() as scraper:
        response = await scraper.scrape("https://example.com")

        if response.status == ScrapStatus.SUCCESS:
            print(response.scrap_html_content)

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 🔐 Creating Session Data

Use the built-in CLI tool to create and store authentication sessions:

```bash
intelliscraper-session --url "https://example.com" --site "example" --output "./example_session.json"
```

**How it works:**

1. 🌐 Opens a Chromium browser with the given URL
2. 🔐 Log in with your credentials
3. ⏎ Press **Enter** after successful login
4. 💾 Session data (cookies, storage, fingerprints) are saved to a JSON file

> [!IMPORTANT]
> Sessions maintain internal time-series data such as timestamps, request durations, and scrape statuses.
> These metrics help analyze performance, rate limits, and stability of scraping sessions.
> Excessive concurrency may cause request failures, so gradual scaling is recommended.

---

## 🧠 Authenticated Asynchronous Scraping with Session

```python
import asyncio
import json
from intelliscraper import AsyncScraper, Session, ScrapStatus

async def main():
    # Load existing session
    with open("example_session.json") as f:
        session = Session(**json.load(f))

    async with AsyncScraper(session_data=session) as scraper:
        response = await scraper.scrape(
            "https://example.com/jobs/python?experience=entry-level%2Cmid-level"
        )

        if response.status == ScrapStatus.SUCCESS:
            print("Successfully scraped authenticated page!")
            print(response.scrap_html_content)

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 📝 HTML Parsing

```python
import asyncio
from intelliscraper import AsyncScraper, HTMLParser, ScrapStatus

async def main():
    async with AsyncScraper() as scraper:
        response = await scraper.scrape("https://example.com")

        if response.status == ScrapStatus.SUCCESS:
            parser = HTMLParser(
                url=response.scrape_request.url,
                html=response.scrap_html_content
            )
            print(parser.text)
            print(parser.links)
            print(parser.markdown)
            print(parser.markdown_for_llm)

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 🌐 Proxy Support (Async)

Use a proxy with this web scraper, utilizing asynchronous blocks.

```python
import asyncio
from intelliscraper import AsyncScraper, BrightDataProxy, ScrapStatus

async def main():
    bright_proxy = BrightDataProxy(
        host="brd.superproxy.io",
        port=22225,
        username="your-username",
        password="your-password"
    )

    async with AsyncScraper(proxy=bright_proxy) as scraper:
        response = await scraper.scrape("https://example.com")

        if response.status == ScrapStatus.SUCCESS:
            print("Scraped successfully through Bright Data proxy!")

if __name__ == "__main__":
    asyncio.run(main())
```

> 📁 **More examples**, including Bright Data configurations and session management, are available in the [`examples/`](./examples) directory.

---

## 📋 Requirements

* Python 3.12+
* Playwright
* Compatible with Windows, macOS, and Linux

---

## 🗺️ Roadmap

* ✅ Async scraping (core feature)
* ✅ Session management CLI
* ✅ Proxy integration (Bright Data)
* ✅ HTML parsing and Markdown generation
* ✅ Anti-detection mechanisms
* 🔄 Distributed crawler mode
* 🔄 AI-based content extraction

---

## 📄 License

Licensed under the **MIT License**.

---

## 📧 Support

For help, issues, or contributions — visit the [GitHub Issues page](https://github.com/omkarmusale0910/IntelliScraper/issues).

---

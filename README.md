# IntelliScraper

A powerful, anti-bot detection web scraping solution built with Playwright, designed for scraping protected sites like Himalayas Jobs and other platforms that require authentication. Features session management, proxy support, and advanced HTML parsing capabilities.

![Python Version](https://img.shields.io/badge/python-3.12%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-active-success)

## ✨ Features

- **🔐 Session Management**: Capture and reuse authentication sessions with cookies, local storage, and browser fingerprints
- **🛡️ Anti-Detection**: Advanced techniques to prevent bot detection
- **🌐 Proxy Support**: Integrated support for Bright Data and custom proxy solutions
- **📝 HTML Parsing**: Extract text, links, and convert to Markdown format (including LLM-optimized output)
- **🎯 CLI Tool**: Easy-to-use command-line interface for session generation
- **⚡ Playwright-Powered**: Built on robust Playwright automation framework

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
> The command above installs Chromium, which is necessary for this library to work.  

> For more reference : https://pypi.org/project/intelliscraper-core/

### Basic Scraping (No Authentication)

```python
from intelliscraper import Scraper, ScrapStatus

# Simple scraping without authentication
scraper = Scraper()
response = scraper.scrape("https://example.com")

if response.status == ScrapStatus.COMPLETED:
    print(response.scrap_html_content)
```

### Creating Session Data

Use the CLI tool to create session data for authenticated scraping. The tool will open a browser where you can manually log in:

```bash
intelliscraper-session --url "https://himalayas.app" --site "himalayas" --output "./himalayas_session.json"
```

**How it works:**
1. 🌐 Opens browser with the specified URL
2. 🔐 You manually log in with your credentials
3. ⏎ Press Enter after successful login
4. 💾 Session data (cookies, storage, fingerprints) saved to JSON file

### Authenticated Scraping with Session

```python
import json
from intelliscraper import Scraper, Session, ScrapStatus

# Load session data
with open("himalayas_session.json") as f:
    session = Session(**json.load(f))

# Scrape with authentication
scraper = Scraper(session_data=session)
response = scraper.scrape("https://himalayas.app/jobs/python?experience=entry-level%2Cmid-level")

if response.status == ScrapStatus.COMPLETED:
    print("Successfully scraped authenticated page!")
    print(response.scrap_html_content)
```

## 📝 HTML Parsing

Parse scraped content to extract text, links, and markdown:

```python
from intelliscraper import Scraper, ScrapStatus, HTMLParser

scraper = Scraper()
response = scraper.scrape("https://example.com")

if response.status == ScrapStatus.COMPLETED:
    # Initialize parser
    parser = HTMLParser(
        url=response.scrape_request.url,
        html=response.scrap_html_content
    )
    
    # Extract different formats
    print(parser.text)              # Plain text
    print(parser.links)             # All links (normalized URLs)
    print(parser.markdown)          # Full markdown
    print(parser.markdown_for_llm)  # Clean markdown for AI (removes nav, footer, ads)
```

The `markdown_for_llm` property is optimized for AI processing - it removes navigation, footers, advertisements, and forms, keeping only useful content.

## 🌐 Proxy Support

IntelliScraper supports proxy configurations including Bright Data and custom solutions:

```python
from intelliscraper import Scraper, ProxyConfig

proxy = ProxyConfig(
    url="http://brd.superproxy.io:22225",
    username="your-username",
    password="your-password"
)

scraper = Scraper(proxy=proxy)
response = scraper.scrape("https://example.com")
```

> 📁 **More examples** including proxy configurations, and advanced usage can be found in the [`examples/`](./examples) folder.

## 📋 Requirements

- Python 3.12+
- Playwright
- Compatible with Windows, macOS, and Linux

## 🗺️ Roadmap

- ✅ Session management with CLI tool
- ✅ Proxy support (Bright Data)
- ✅ HTML parsing and Markdown conversion
- ✅ Anti-detection features
- 🔄 PyPI package (Coming soon)
- 🔄 Async scraping support
- 🔄 Web crawler
- 🔄 AI integration

## 📄 License

This project is licensed under the MIT License.


## 📧 Support

For issues, questions, or contributions, please visit our [GitHub repository's issues page](https://github.com/omkarmusale0910/IntelliScraper/issues).

---

**Note**: This project is under active development. The package will be available on PyPI in the coming weeks.
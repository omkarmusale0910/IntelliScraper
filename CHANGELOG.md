# Changelog

All notable changes to IntelliScraper will be documented in this file.

## 0.1.3 - 2025-11-07
- Updated Scraper from synchronous to asynchronous implementation to significantly improve concurrency, performance, and resource efficiency.

## 0.1.2 - 2025-10-18
- Added per-session success and failure counters to help monitor scraping reliability and session performance.

## 0.1.1 - 2025-10-17
- Minor update in `README.md`: added Playwright installation instructions.

## 0.1.0 - 2025-10-17

### Added
- Initial release
- Web scraping with Playwright
- Session management for authenticated scraping
- CLI tool for session generation (`intelliscraper-session`)
- HTML parsing (text, links, markdown, markdown_for_llm)
- Anti-detection features
- Proxy support (Bright Data and custom)

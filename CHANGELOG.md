# Changelog

All notable changes to IntelliScraper will be documented in this file.

## 0.1.6 - 2026-05-01

### Fixed
- Fixed the issue with the `html-to-markdown` library and updated to use the latest version (3.3.2). Added support for extracting `navigable_links`.

## 0.1.5 - 2026-05-01

### Fixed
- Re-release of 0.1.4 fix due to PyPI version conflict. The 0.1.4 wheel was uploaded without the build fix, so 0.1.5 contains the corrected package configuration ensuring `intelliscraper` is importable after installation.

## 0.1.4 - 2026-05-01

### Fixed
- Fixed package build configuration that prevented importing `intelliscraper` after installation. The wheel was incorrectly configured to package a non-existent directory (`intelliscraper-core`) instead of the actual source directory (`intelliscraper`), causing `ModuleNotFoundError` on import.

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

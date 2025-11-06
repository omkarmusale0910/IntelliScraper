"""
Simple Example: Using AsyncScraper with Session Data

This example shows the minimal code needed to scrape multiple URLs
with session authentication.
"""

# For detailed instructions and advanced usage examples, refer to the IntelliScraper/examples/session_usage.md

import asyncio
import json

from intelliscraper import AsyncScraper, ScrapStatus, Session


async def main():
    """Main async function to scrape multiple URLs with session."""

    #  Define URLs to scrape
    urls = [
        "https://www.example.com/protected/page1",
        "https://www.example.com/protected/page2",
        "https://www.example.com/protected/page3",
        "https://www.example.com/protected/page4",
    ]

    #  Load session data from JSON file
    with open("example_session.json", "r") as f:
        session_data = json.load(f)

    #  Create Session object
    session = Session(**session_data)

    #  Use AsyncScraper with session
    async with AsyncScraper(
        headless=False,  # Set to True to hide browser
        session_data=session,  # Pass session for authentication
        max_concurrent_pages=4,  # Scrape 4 URLs in parallel
    ) as scraper:

        #  Create tasks for all URLs
        tasks = [scraper.scrape(url) for url in urls]

        #  Await gathering all tasks
        results = await asyncio.gather(*tasks)

    #  Process results
    for i, result in enumerate(results, 1):
        if result.status in (ScrapStatus.SUCCESS, ScrapStatus.PARTIAL_SUCCESS):
            print(f"✓ URL {i}: Success ({len(result.scrap_html_content)} bytes)")

            # Save HTML to file
            with open(f"output_{i}.html", "w", encoding="utf-8") as f:
                f.write(result.scrap_html_content)
        else:
            print(f"✗ URL {i}: Failed - {result.error_msg}")


if __name__ == "__main__":
    asyncio.run(main())

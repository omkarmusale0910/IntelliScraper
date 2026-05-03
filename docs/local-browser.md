# Local Browser Mode (CDP)

Connect to your running Chrome instance to reuse existing logins ideal for sites like LinkedIn, Gmail, or any site with complex authentication.

## How It Works

1. IntelliScraper checks if Chrome is running with `--remote-debugging-port=9222`.
2. If not, it auto-launches Chrome using the debug profile.
3. Connects via the Chrome DevTools Protocol (CDP) and reuses the existing browser context **all cookies and logins are preserved**.
4. Only the pages opened by IntelliScraper are closed on exit your Chrome session stays running.

## Setup (One-Time)

### Step 1: Create the Debug Profile

```bash
make chrome-debug-profile
```

This creates a separate Chrome profile at `~/.config/google-chrome-debug`.

```{warning}
The debug profile is **separate** from your default Chrome profile. You must log into target sites in this profile before scraping.
```

### Step 2: Log Into Target Sites

```bash
make chrome-debug-login URL=https://www.linkedin.com
```

This opens Chrome with the debug profile.  Log in to the site, then close Chrome.

Repeat for each site you want to scrape:

```bash
make chrome-debug-login URL=https://www.linkedin.com
make chrome-debug-login URL=https://mail.google.com
```

### Step 3: Use in Code

```python
import asyncio
from intelliscraper import AsyncScraper, ScrapStatus

async def main():
    async with AsyncScraper(
        use_local_browser=True,
        headless=False,
    ) as scraper:
        response = await scraper.scrape(
            "https://www.linkedin.com/jobs/collections/recommended/"
        )

        if response.status == ScrapStatus.SUCCESS:
            print(f"HTTP {response.http_status_code}")
            print(f"Browser mode: {response.browser_mode}")
            print(response.scrap_html_content[:500])

asyncio.run(main())
```

## Configuration Options

`LocalBrowserBackend` accepts these parameters (passed through `AsyncScraper`):

| Parameter             | Default   | Description                                  |
| --------------------- | --------- | -------------------------------------------- |
| `use_local_browser` | `False` | Enable local browser mode                    |
| `headless`          | `True`  | If Chrome needs auto-launching, run headless |

The backend internally uses:

| Constant      | Value                             | Description                           |
| ------------- | --------------------------------- | ------------------------------------- |
| CDP port      | `9222`                          | Chrome DevTools Protocol port         |
| Max wait      | `20s`                           | Timeout waiting for Chrome to start   |
| Poll interval | `1.0s`                          | How often to check if Chrome is ready |
| Profile dir   | `~/.config/google-chrome-debug` | Chrome user data directory            |

## Troubleshooting

### Chrome is not reachable

```
LocalBrowserConnectionError: Chrome not reachable on port 9222 after 20s.
```

**Fix:** Close all Chrome windows, then start Chrome with the debug profile:

```bash
make chrome-debug-login URL=https://example.com
```

### Profile lock error

If Chrome says the profile is locked, another Chrome process is using it:

```bash
make chrome-debug-stop
```

Then retry.

### Authentication expired

If scraping returns login pages, your session has expired.  Re-authenticate:

```bash
make chrome-debug-login URL=https://www.linkedin.com
```

Log in again, close Chrome, then retry your scraper.

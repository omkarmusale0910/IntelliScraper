# AsyncScraper with Session - Simple Example

This example demonstrates how to scrape authenticated pages using AsyncScraper with session data.

## Files

- `scraping_with_session.py` - Main script with scraping code
- `example_session.json` - Sample session file (replace with your actual session)

## Quick Start

### 1. Generate Session Data (Recommended Way)

Instead of manually copying cookies, you can automatically generate session data using the built-in session script.

Run the following command:

```bash
intelliscraper-session --url "https://www.example.com/" --site "example" --output "./example_session.json"
```

What This Does

- Opens an interactive browser window for the given URL (--url).

- If the site requires login, log in manually using your credentials inside that window.

- Once you’re logged in successfully, press Enter in the terminal.

- The script will automatically extract all cookies, localStorage, and sessionStorage data from your active browser session.

- All session details are then saved into the file specified by --output (e.g., example_session.json).

- You can then use this session file in your scraper to access authenticated pages seamlessly.

### 2. Run the Script
```bash
uv examples/scraping_with_session.py
```

### 3. Check Output

The script will create files:
- `output_1.html` - Content from first URL
- `output_2.html` - Content from second URL...

## Configuration Options

### Headless Mode
```python
headless=True   # Run browser in background (no visible window)
headless=False  # Show browser window (useful for debugging)
```

### Concurrent Pages
```python
max_concurrent_pages=4  # Scrape 4 URLs at the same time
max_concurrent_pages=8  # Scrape 8 URLs at the same time
```

## Troubleshooting

### Issue: "Session expired" or redirect to login

**Solution:** Your session has expired. Export a fresh session from your browser.

### Issue: Empty HTML or missing content

**Solution:** 
1. Try with `headless=False` to see what's happening
2. Increase timeout: `timeout=timedelta(seconds=60)`
3. Check if the site requires JavaScript execution time

## Need Help?

- Check the main documentation
- Review error messages in console
- Try with `headless=False` to debug visually
.ONESHELL: 
SHELL := /bin/bash
PYTHON_VERSION := $(shell cat .python-version)

# Development 
clean:
	rm -rf .venv
	uv cache clean

uv-init-venv: clean
	uv venv --python $(PYTHON_VERSION)

format:
	uv run -- black . -q
	uv run -- isort --profile black .

install: uv-init-venv
	source .venv/bin/activate && uv sync --frozen
	source .venv/bin/activate && uv pip install -e .
	source .venv/bin/activate && uv pip install --group dev

playwright-chromium:
	source .venv/bin/activate && uv run -- playwright install chromium

test: install playwright-chromium
	uv run -- pytest -vv .

# Chrome Debug Profile (Local Browser Mode) 
#
# IntelliScraper's local browser mode connects to Chrome via CDP.
# These commands help you set up and manage the debug profile.
#
# Workflow:
#   1. make chrome-debug-profile       # Create the profile directory
#   2. make chrome-debug-login URL=https://www.linkedin.com
#                                       # Log into target sites
#   3. Close Chrome
#   4. Use AsyncScraper(use_local_browser=True) in your code

chrome-debug-profile:  ## Create Chrome debug profile for local browser mode
	@echo "Creating Chrome debug profile at ~/.config/google-chrome-debug..."
	@mkdir -p $$HOME/.config/google-chrome-debug
	@echo ""
	@echo "✓ Profile directory created."
	@echo ""
	@echo "Next steps:"
	@echo "  1. Log into your target sites:"
	@echo "     make chrome-debug-login URL=https://www.linkedin.com"
	@echo ""
	@echo "  2. After logging in, close Chrome"
	@echo ""
	@echo "  3. Use in your code:"
	@echo '     async with AsyncScraper(use_local_browser=True) as scraper:'
	@echo '         result = await scraper.scrape("https://linkedin.com/jobs")'

chrome-debug-login:  ## Open Chrome with debug profile to log into sites (URL=https://...)
	@test -n "$(URL)" || (echo "Usage: make chrome-debug-login URL=https://linkedin.com" && exit 1)
	@echo "Opening Chrome with debug profile..."
	@echo "Log into the site, then close Chrome when done."
	google-chrome \
		--remote-debugging-port=9222 \
		--user-data-dir="$$HOME/.config/google-chrome-debug" \
		--profile-directory="Default" \
		--no-first-run --no-default-browser-check \
		"$(URL)"

chrome-debug-stop:  ## Stop the Chrome debug instance
	@pkill -f "google-chrome-debu[g]" 2>/dev/null || true
	@echo "✓ Chrome debug instance stopped."

.PHONY: clean uv-init-venv format install playwright-chromium test \
	chrome-debug-profile chrome-debug-login chrome-debug-stop \
	install-docs docs

# Documentation
install-docs: uv-init-venv
	source .venv/bin/activate && uv pip install -e .[docs]

docs: install-docs
	source .venv/bin/activate && sphinx-build -b html docs docs/_build/html
	@echo "✓ Documentation built at docs/_build/html/index.html"
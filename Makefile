.ONESHELL: 
SHELL := /bin/bash
PYTHON_VERSION := $(shell cat .python-version)

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
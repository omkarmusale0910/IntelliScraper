.ONESHELL: 
SHELL := /bin/bash

format:
	uv run -- black . -q
	uv run -- isort --profile black .


install:
	uv sync

playwright-chromium:
	playwright install chromium

test: install playwright-chromium
	uv run -- pytest -vv -k .
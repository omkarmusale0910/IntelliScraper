.ONESHELL: 
SHELL := /bin/bash

format:
	uv run -- black . -q
	uv run -- isort --profile black .


install:
	uv sync

playwright-cromium:
	playwright install chromium

test: install playwright-cromium
	uv run -- pytest -vv -k .
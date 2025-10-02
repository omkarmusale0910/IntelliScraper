.ONESHELL: 

format:
	uv run -- black . -q
	uv run -- isort --profile black .

install:
	uv sync

playwrite-cromium: install
	playwrite install chromium


FROM python:3.12-slim-bookworm

RUN apt-get update 

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

RUN --mount=type=cache,target=/root/.catch/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv export --format requirements-txt -o requirements.txt

RUN pip install -r requirements.txt

RUN uv run -- playwright install chromium

COPY . .
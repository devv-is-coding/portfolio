# syntax=docker/dockerfile:1
# FastAPI backend, following uv's Docker guide. Two targets:
#   dev     -> `fastapi dev` with reload, source synced in by `docker compose up --watch` (compose.yaml)
#   runtime -> production `fastapi run`, no dev tooling (compose.prod.yaml, default target)

ARG PYTHON_VERSION=3.13
ARG UV_VERSION=0.9.21

FROM ghcr.io/astral-sh/uv:${UV_VERSION} AS uv

FROM python:${PYTHON_VERSION}-slim AS base
COPY --from=uv /uv /uvx /bin/
ENV UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0 \
    UV_CACHE_DIR=/tmp/uv-cache \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"
RUN groupadd --system --gid 10001 app \
    && useradd --system --uid 10001 --gid app --home-dir /app app
WORKDIR /app

# --- Development: fastapi dev, owned by `app` so watch can sync into /app ----
FROM base AS dev
RUN chown app:app /app
USER app
RUN --mount=type=cache,target=/tmp/uv-cache,uid=10001,gid=10001 \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-dev
COPY --chown=app:app . .
EXPOSE 8000
CMD ["fastapi", "dev", "--host", "0.0.0.0", "--port", "8000"]

# --- Production build: locked deps into /app/.venv ---------------------------
FROM base AS builder
ENV UV_COMPILE_BYTECODE=1
RUN --mount=type=cache,target=/tmp/uv-cache \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-dev
COPY . .
RUN --mount=type=cache,target=/tmp/uv-cache \
    uv sync --locked --no-dev

# --- Production runtime: Python + venv + app, no uv --------------------------
FROM python:${PYTHON_VERSION}-slim AS runtime
RUN groupadd --system --gid 10001 app \
    && useradd --system --uid 10001 --gid app --home-dir /app app
WORKDIR /app
COPY --from=builder --chown=app:app /app /app
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1
USER app
EXPOSE 8000
# Entrypoint (app.main:app) comes from [tool.fastapi] in pyproject.toml.
CMD ["fastapi", "run", "--port", "8000"]

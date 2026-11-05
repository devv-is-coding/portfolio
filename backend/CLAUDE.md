# Backend (FastAPI)

FastAPI API for the portfolio. Python 3.13, Pydantic v2, pydantic-settings, managed with **uv**. Run every command from `backend/`.

## Commands

```bash
uv sync                            # install / update the venv from uv.lock
uv run fastapi dev                 # dev server with reload, http://localhost:8000 (docs at /docs)
uv run ruff check . --fix          # lint
uv run ruff format .               # format
uv run mypy app tests              # type check (strict)
uv run pytest                      # tests
```

Before finishing a task, run `uv run ruff check . && uv run ruff format --check . && uv run mypy app tests && uv run pytest` and fix every failure. CI runs exactly these.

## Conventions

@../.ai/rules/backend.md

## Working notes

- The app entrypoint (`app.main:app`) is set in `pyproject.toml` under `[tool.fastapi]`, so `fastapi dev` / `fastapi run` need no path argument.
- The frontend runs at `http://localhost:3000` and is allowed by the default `CORS_ORIGINS`. Add production origins through the environment, not in code.
- Never import from `../frontend`. The two apps talk only over HTTP.

# Backend (FastAPI)

FastAPI API for the portfolio. Python 3.13, Pydantic v2, pydantic-settings, SQLAlchemy 2 (async) + Alembic on MariaDB, Redis, Celery, managed with **uv**. Run every command from `backend/`.

## Commands

```bash
uv sync                            # install / update the venv from uv.lock
uv run fastapi dev                 # dev server with reload, http://localhost:8000 (docs at /docs)
uv run ruff check . --fix          # lint
uv run ruff format .               # format
uv run mypy app tests alembic      # type check (strict)
uv run pytest                      # tests
```

Before finishing a task, run `uv run ruff check . && uv run ruff format --check . && uv run mypy app tests alembic && uv run pytest` and fix every failure. CI runs exactly these, plus the migration checks below.

**Always check the backend's health before ending a task**, even when the checks pass. Passing tests on the host don't prove the running API works.

1. Make sure the dev stack is running (`docker compose up --watch` from the repo root; start it in the background if it isn't).
2. Run `curl -fsS http://localhost:8000/health`. It must return `{"status":"ok"}`. This also proves MariaDB is reachable: `/health` runs `SELECT 1` and returns 503 when the database is down.
3. Run `docker compose ps backend`. It must show `(healthy)`.

If either fails, read `docker compose logs backend`, fix the cause, and check again. Never report a task as done while the health check fails.

## Database migrations (Alembic)

Run Alembic **on the host** from `backend/`. It connects to the Docker MariaDB on `localhost:3307` (the defaults in `backend/.env`). Generated files must be created on the host, because watch sync is one-way.

```bash
uv run alembic revision --autogenerate -m "create users table"   # new migration from model changes
uv run alembic upgrade head                                       # apply all pending migrations
uv run alembic downgrade -1                                       # roll back the last migration
uv run alembic downgrade base                                     # roll back everything
uv run alembic current                                            # revision the database is on
uv run alembic history                                            # list all migrations
uv run alembic check                                              # fail if models changed without a migration
uv run alembic upgrade head --sql                                 # print the SQL instead of running it
```

Workflow for every schema change:

1. Change or add a model in `app/models/`. A new model module must be imported in `app/models/__init__.py`, or autogenerate won't see it.
2. `uv run alembic revision --autogenerate -m "<what changed, lowercase>"`, e.g. `"create users table"`, `"add avatar url to users"`. Ruff fixes and formats the new file automatically.
3. **Read the generated file in `alembic/versions/`** before applying it. Autogenerate can't detect table/column renames (it drops and re-creates them, losing data) and some type changes. Fix `upgrade()` and `downgrade()` by hand when needed.
4. `uv run alembic upgrade head`, then `uv run alembic downgrade -1` and `uv run alembic upgrade head` again, to prove the migration is reversible.
5. `uv run alembic check` must print "No new upgrade operations detected."

Rules:
- Never edit a migration that has been merged into `main`. Fix a mistake with a new migration.
- Never change the database schema by hand or with `Base.metadata.create_all()`; every change goes through a migration.
- One migration per logical change; commit the model change and its migration together.
- The `migrate` service applies `alembic upgrade head` on every `docker compose up`. To apply a new migration while the stack is running, run `uv run alembic upgrade head` on the host (or `docker compose run --rm migrate` from the repo root).
- CI runs `alembic upgrade head`, `alembic check`, `alembic downgrade base` and `alembic upgrade head` against a real MariaDB, so a broken or missing migration fails CI.

## Background jobs (Celery) and Redis

- The Celery app is `app/worker.py`; tasks live in `app/tasks/<area>.py` and are listed in `include` in `app/worker.py`.
- The `worker` service runs `celery -A app.worker worker --loglevel=info`. Watch syncs code into it and restarts it, because Celery doesn't auto-reload.
- Check the worker: `docker compose exec -T backend python -c "from app.tasks.system import ping; print(ping.delay().get(timeout=20))"` prints `pong`.
- Redis is the cache (`RedisDep` from `app/core/redis.py`) and the Celery broker/result backend (`REDIS_URL`, host port 6380).

## Conventions

@../.ai/rules/backend.md

## Working notes

- The app entrypoint (`app.main:app`) is set in `pyproject.toml` under `[tool.fastapi]`, so `fastapi dev` / `fastapi run` need no path argument.
- The frontend runs at `http://localhost:3000` and is allowed by the default `CORS_ORIGINS`. Add production origins through the environment, not in code.
- Never import from `../frontend`. The two apps talk only over HTTP.
- Secrets live in `backend/.env` (gitignored) locally and in the hosting platform's environment variables in production. Every variable must be documented in `backend/.env.example` without its real value.
- Keep `backend/progress.md` (gitignored) up to date: tick off finished items, add new ones under **Next**, and add a dated **Log** entry for each finished task.

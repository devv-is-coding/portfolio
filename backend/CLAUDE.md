# Backend (FastAPI)

Python 3.13, FastAPI, Pydantic v2, SQLAlchemy 2 async + Alembic on MariaDB, Redis, Celery, managed with uv. Run everything from `backend/`. Never import from `../frontend`.

## Before ending a task that edited backend files

1. Checks (CI runs the same): `uv run ruff check . && uv run ruff format --check . && uv run mypy app tests alembic && uv run pytest`
2. Pylance: no errors in the editor's diagnostics for the changed files, and `uv run --with pyright pyright app tests alembic` clean.
3. Health: with `docker compose up --watch` running, `curl -fsS http://localhost:8000/health` returns `{"status":"ok"}` and `docker compose ps backend` shows `(healthy)`. If not, read `docker compose logs backend` and fix it.

## Migrations (Alembic, on the host; MariaDB at localhost:3307)

```bash
uv run alembic revision --autogenerate -m "create users table"
uv run alembic upgrade head
uv run alembic downgrade -1
uv run alembic check
```

- New model modules must be imported in `app/models/__init__.py`.
- Read every generated migration before applying it (autogenerate turns renames into drop + create). Then upgrade, `downgrade -1`, upgrade, and `alembic check` must report no changes.
- Never edit a merged migration, never change the schema by hand or with `create_all()`. Commit a model change with its migration.

## Celery and Redis

- Tasks: `app/tasks/<area>.py`, `@celery_app.task(name="<area>.<action>")`, listed in `include` in `app/worker.py`. JSON-serializable arguments only.
- Worker check: `MSYS_NO_PATHCONV=1 docker compose exec -T backend python -c "from app.tasks.system import ping; print(ping.delay().get(timeout=20))"` prints `pong`.

## Conventions

@../.ai/rules/backend.md

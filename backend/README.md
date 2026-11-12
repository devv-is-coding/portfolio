# Portfolio API (backend)

FastAPI backend of the portfolio: public read endpoints for the site and admin endpoints
to manage its content. Python 3.13, FastAPI, Pydantic v2, SQLAlchemy 2 (async) with
Alembic on MariaDB 11.8, Redis, Celery, managed with [uv](https://docs.astral.sh/uv/).
Files live in [ImageKit](https://imagekit.io).

Interactive API docs: http://localhost:8000/docs (OpenAPI at `/openapi.json`).

## Contents

- [Run it with Docker](#run-it-with-docker)
- [Run it natively](#run-it-natively)
- [Commands](#commands)
- [Configuration](#configuration)
- [Architecture](#architecture)
- [API conventions](#api-conventions)
- [Background jobs](#background-jobs)
- [Performance](#performance)
- [Production](#production)

## Run it with Docker

Needs Docker Desktop. From the repository root:

```bash
cp backend/.env.example backend/.env   # optional locally: the defaults work
docker compose up --watch
```

This starts MariaDB (host port 3307), Redis (6380), a one-off `migrate` job
(`alembic upgrade head`), the API on http://localhost:8000, the Celery `worker` (with the
beat scheduler inside it), and the frontend. `--watch` syncs your edits into the
containers; the API reloads, the worker restarts.

Create the admin account (you're asked for the password twice):

```bash
docker compose exec backend python -m app.commands.create_admin --email you@example.com
```

In Git Bash, prefix `docker compose exec` with `MSYS_NO_PATHCONV=1`. After changing
`backend/.env`, recreate the containers that read it:
`docker compose up -d --force-recreate backend worker`.

## Run it natively

MariaDB and Redis still come from Docker; the API runs on your machine:

```bash
docker compose up -d mariadb redis
cd backend
cp .env.example .env          # its defaults point at localhost:3307 and :6380
uv sync
uv run alembic upgrade head
uv run python -m app.commands.create_admin --email you@example.com
uv run fastapi dev            # http://localhost:8000, reloads on changes
```

Background jobs, in another terminal (the worker with the beat scheduler inside it):

```bash
uv run celery -A app.worker worker --beat --loglevel=info --schedule /tmp/celerybeat-schedule
```

On Windows the embedded scheduler doesn't work: run `uv run celery -A app.worker worker
--pool=solo --loglevel=info`, and beat in a third terminal with
`uv run celery -A app.worker beat --loglevel=info --schedule %TEMP%\celerybeat-schedule`.

## Commands

Run from `backend/`.

| What | Command |
| --- | --- |
| All checks (as CI) | `uv run ruff check . && uv run ruff format --check . && uv run mypy app tests alembic && uv run pytest` |
| Pylance / Pyright | `uv run --with pyright pyright app tests alembic` |
| Integration tests must run | `TESTS_REQUIRE_DATABASE=1 uv run pytest` (otherwise skipped without MariaDB) |
| New migration | `uv run alembic revision --autogenerate -m "add x to y"` (read it before applying) |
| Apply / undo migrations | `uv run alembic upgrade head` / `uv run alembic downgrade -1` |
| Models match migrations | `uv run alembic check` |
| Admin account | `uv run python -m app.commands.create_admin --email you@example.com [--reset-password]` |
| Test data | `uv run python -m app.commands.seed` (add) / `--clear` (remove) |
| Load test | `uv run python -m app.commands.load_test [--base-url URL] [--requests 500] [--concurrency 100]` |
| Dependency audit | `uv export --frozen --no-emit-project --format requirements-txt > req.txt && uvx pip-audit -r req.txt --disable-pip` |

Notes:

- The integration tests run against the configured MariaDB inside a transaction that is
  rolled back, so they never change data. They expect no seed data: run
  `seed --clear` before `pytest`.
- `seed` refuses to run with `ENVIRONMENT=production`. Every seeded row is marked
  (`seed-` slugs and file ids, `@seed.example.com` emails), so `--clear` removes only
  those.
- Dependencies: `uv add <package>` (or `uv add --dev`), never pip; commit
  `pyproject.toml` with `uv.lock`.

## Configuration

All settings are environment variables, read by `app/core/config.py` (`Settings`).
Locally they come from `backend/.env` (copy `.env.example`; never commit `.env`); in
production from the hosting platform. `tests/test_openapi.py` fails if a setting is
missing from `.env.example`.

| Variable | Default | What |
| --- | --- | --- |
| `APP_NAME` | `Portfolio API` | Title in the API docs. |
| `ENVIRONMENT` | `development` | `production` turns on HSTS and the production checks below. |
| `CORS_ORIGINS` | `["http://localhost:3000"]` | JSON list of exact frontend origins (no path, never `*`; https in production). |
| `MAX_REQUEST_BODY_BYTES` | `1048576` | Larger request bodies get 413. |
| `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` | local Docker values | MariaDB connection. |
| `DB_POOL_SIZE`, `DB_MAX_OVERFLOW` | `5`, `10` | Connection pool per API process. |
| `REDIS_URL` | `redis://localhost:6380/0` | Rate limits and the Celery broker. |
| `CELERY_WORKER_CONCURRENCY` | `1` | Celery worker processes (each ~50 MB). |
| `SENTRY_DSN`, `SENTRY_TRACES_SAMPLE_RATE` | empty, `0.1` | Error monitoring; off without a DSN. |
| `IMAGEKIT_PUBLIC_KEY`, `IMAGEKIT_PRIVATE_KEY`, `IMAGEKIT_URL_ENDPOINT` | empty | ImageKit account; media endpoints answer 503 without them; required in production. |
| `LOG_LEVEL`, `LOG_FORMAT` | `INFO`, `text` | `json` writes one JSON object per line (use it in production). |
| `JWT_SECRET_KEY` | development key | Signs access tokens; 32+ random characters, required in production. |
| `ACCESS_TOKEN_EXPIRE_MINUTES`, `REFRESH_TOKEN_EXPIRE_DAYS` | `15`, `30` | Token lifetimes. |
| `LOGIN_MAX_ATTEMPTS`, `LOGIN_WINDOW_SECONDS` | `5`, `900` | Failed logins per IP before 429. |
| `CONTACT_MAX_MESSAGES`, `CONTACT_WINDOW_SECONDS` | `5`, `3600` | Contact messages per IP before 429. |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_STARTTLS`, `SMTP_FROM` | empty, `587`, empty, empty, `true`, empty | Outgoing email for contact notifications. |
| `CONTACT_NOTIFY_EMAIL` | empty | Who gets the notification; no email is sent without it. |
| `WEB_CONCURRENCY` | `1` | API processes (read by uvicorn under `fastapi run`). |
| `FORWARDED_ALLOW_IPS` | `127.0.0.1,::1` | Proxies trusted for `X-Forwarded-For` (read by uvicorn). |

Secrets (`DB_PASSWORD`, `JWT_SECRET_KEY`, `IMAGEKIT_PRIVATE_KEY`, `SMTP_PASSWORD`) belong
only in `.env` or the platform's settings, never in code, `.env.example` or images.

## Architecture

```
app/
  main.py          the app: middleware, routers, OpenAPI description
  routers/         HTTP only: parse the request, call one service function, return a schema
  services/        business rules, the transaction (commit) and the audit entry
  repositories/    SQLAlchemy queries, never commit
  models/          tables (one module each), enums with their stored codes
  schemas/         request and response models (Pydantic), limits match the columns
  core/            config, database, errors, pagination, logging, security, ImageKit, email,
                   HTTP caching and security middleware
  tasks/           Celery tasks; worker.py holds the Celery app and the beat schedule
  commands/        CLI tools: create_admin, seed, load_test
alembic/           migrations (one per model change, reviewed before applying)
tests/             unit tests (no services needed) and tests/integration (MariaDB)
```

A request goes **router → service → repository → model**. Services raise the errors in
`app/core/errors.py`; shared write steps (save, audit, commit) live in
`app/services/crud.py`. Status columns are stored as small integer codes
(`app/models/enums.py`); the API uses the readable values (`"draft"`).

## API conventions

- **Public routes** (`/profile`, `/projects`, `/blog/posts`, ...) return published content
  only and need no token. Drafts and archived items answer 404.
- **Admin routes** (`/admin/...`) need `Authorization: Bearer <access token>`.
  `POST /auth/login` returns an access token (15 minutes) and a refresh token (30 days);
  `POST /auth/refresh` swaps the refresh token for a new pair (reusing an old one logs
  every session out), `POST /auth/logout` revokes it. Every admin change is written to
  the audit log (`GET /admin/audit-logs`).
- **Errors** always have one shape:
  ```json
  {"error": {"code": "validation_error", "message": "Invalid request",
             "details": [{"field": "body.title", "message": "...", "type": "string_too_short"}]}}
  ```
  Codes: `not_found` (404), `conflict` (409, e.g. a taken slug), `validation_error` (422,
  never echoing the values sent), `unauthorized` (401), `rate_limited` (429 with
  `Retry-After`), `payload_too_large` (413), `bad_gateway` (502, ImageKit failed),
  `service_unavailable` (503), `internal_error` (500, never with details).
- **Lists** take `page` (from 1), `size` (1–100, default 20), and where offered `sort`
  (comma-separated fields, `-` for descending, e.g. `-published_at,title`; unknown
  fields are 422) and `q` (case-insensitive search). They return
  `{"items": [...], "total": 42, "page": 1, "size": 20, "pages": 3}`.
- **Slugs** are made from the title or name when left out; send one explicitly for
  titles without Latin letters.
- **Media**: the browser uploads to ImageKit with a signature from
  `GET /admin/media/upload-auth`, then registers the file with `POST /admin/media`.
  Other resources reference media by id (`thumbnail_media_id`, ...); reads return the URL.
- **Caching**: public `GET` responses carry an `ETag` and `Cache-Control: public,
  no-cache`; send the ETag back as `If-None-Match` and an unchanged response is a 304
  without a body. Admin, auth and health responses are `no-store`. Responses over 1 KB
  are gzipped when the client accepts it.
- **Limits**: failed logins and contact messages are limited per client IP (429). The
  contact form has a hidden `website` field: when it's filled, the message is accepted
  but dropped.

## Background jobs

| Task | When | What |
| --- | --- | --- |
| `media.delete_file` | after `DELETE /admin/media/{id}` | Deletes the file in ImageKit (retries with backoff). |
| `contact.notify_admin` | after a contact message, when SMTP is set | Emails `CONTACT_NOTIFY_EMAIL` (retries with backoff). |
| `auth.cleanup_refresh_tokens` | daily at 03:00 UTC (beat) | Deletes refresh tokens that expired over 7 days ago. |
| `system.ping` | on demand | Worker check: returns `pong`. |

Beat runs inside the worker (`--beat`), which is right for one worker. Exactly one beat
may run, or scheduled tasks run twice: with a second worker, drop `--beat` and run
`celery -A app.worker beat` as its own service. Worker and beat log in the same format as
the API, with the task id where the API puts the request id.

## Performance

Measured with `seed` and `load_test` (details in the project plan):

- One request at a time, every public read answers in 4–12 ms (p95) on the dev server.
- Each public read uses a fixed number of SQL queries (1–3, whatever the page size);
  `tests/integration/test_query_budget.py` fails if a change adds one.
- Indexes back every list's default sort and filters (checked with `EXPLAIN`).
- Throughput scales with processes: one production process serves about 155–520
  requests a second per endpoint, with no errors at 50 concurrent requests; add
  processes with `WEB_CONCURRENCY` only when traffic needs it.

Footprint of the production stack, sized for a small server (measured idle; about
310 MB after a load test):

| Container | Memory | Why so small |
| --- | --- | --- |
| API (`fastapi run`, 1 process) | ~98 MB | `WEB_CONCURRENCY=1` |
| Worker (Celery, with beat inside) | ~107 MB | one thread (`--pool=threads`, `CELERY_WORKER_CONCURRENCY=1`), beat embedded with `--beat` |
| MariaDB | ~65 MB | 64 MB buffer pool, 8 MB key and log buffers (the data is a few MB) |
| Redis | ~6 MB | |
| **Backend total** | **~276 MB** | was ~1,350 MB with Celery's defaults and a separate beat |

## Production

The production image (`Dockerfile`, default target) runs `fastapi run` as a non-root
user; `compose.prod.yaml` runs it with MariaDB, Redis, the worker (with beat) and the frontend.
Before going live:

- Set `ENVIRONMENT=production`, your own `JWT_SECRET_KEY`, the ImageKit keys, the
  database and Redis settings, `CORS_ORIGINS` (https), and `LOG_FORMAT=json`. The API
  refuses to start without the JWT key and ImageKit settings.
- `WEB_CONCURRENCY` (default 1, ~100 MB each): one API process serves a portfolio
  easily; on a bigger server, one or two per CPU core. Keep
  `WEB_CONCURRENCY × (DB_POOL_SIZE + DB_MAX_OVERFLOW)` below MariaDB's
  `max_connections` (151 by default), with room for the worker and migrations.
- Behind a proxy or the Next.js server, set `FORWARDED_ALLOW_IPS` to its address (or
  CIDR) so the per-IP limits see visitors. Never `*` while the API is also reachable
  directly: clients could fake their IP.
- Migrations run with `alembic upgrade head` before the new version starts (the
  `migrate` service in both compose files does this).
- The API docs (`/docs`, `/openapi.json`) stay public; admin routes still need a token.

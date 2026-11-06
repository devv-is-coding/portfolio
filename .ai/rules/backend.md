---
paths:
  - 'backend/**'
---

<!--
  Backend (FastAPI) rules. Claude Code must follow these when working in backend/.
  Loaded by backend/CLAUDE.md. Enforced by ruff, mypy (strict), pytest and CI.
-->

# Backend conventions (FastAPI)

Python 3.13, FastAPI, Pydantic v2, pydantic-settings, SQLAlchemy 2 (async) + Alembic on MariaDB (asyncmy), Redis, Celery, PyJWT, pwdlib[argon2], HTTPX, Sentry, managed with **uv**. All paths below are relative to `backend/`. Run everything from `backend/`:

```bash
uv run fastapi dev                 # dev server with reload (entrypoint set in pyproject.toml)
uv run ruff check . --fix          # lint (+ autofix)
uv run ruff format .               # format
uv run mypy app tests alembic      # type check (strict)
uv run pytest                      # tests
uv run alembic upgrade head        # apply migrations (see backend/CLAUDE.md for the full workflow)
```

CI (`.github/workflows/ci.yml`, job **Backend**) runs `ruff check`, `ruff format --check` and `mypy`, then `alembic upgrade head` and `alembic check` against MariaDB, then `pytest` (integration tests included), then `alembic downgrade base` and `alembic upgrade head`, on every push and pull request. Fix every failure before finishing a task.

## Folder structure

```
app/
  main.py            Creates the FastAPI app: lifespan, middleware, CORS, include_router(...). No endpoints here.
  worker.py          Celery app (broker/result backend = Redis)
  core/config.py     Settings (pydantic-settings) + get_settings()
  core/database.py   Async engine, SessionLocal, get_session / SessionDep
  core/redis.py      Async Redis client, get_redis / RedisDep
  core/sentry.py     init_sentry() (only when SENTRY_DSN is set)
  dependencies.py    Shared dependencies (auth, current user, ...) when needed
  models/            SQLAlchemy models, one module per table; base.py holds Base and mixins, enums.py the status enums; import each in __init__.py
  routers/           One APIRouter per resource: projects.py, contact.py, health.py
  schemas/           Pydantic request/response models, one module per resource
  services/          Business logic; routers stay thin and call services
  tasks/             Celery tasks, one module per area; register each in worker.py `include`
  commands/          CLI scripts, run as `python -m app.commands.<name>` (argparse, no extra dependencies)
alembic/
  env.py             Async migration env; URL from Settings, metadata from app.models
  versions/          Migration files (generated, then reviewed by hand)
tests/
  conftest.py        Shared fixtures (TestClient, dependency overrides, ...)
  test_<module>.py   Tests, mirroring app/ (routers/test_projects.py for larger suites)
```

Add `services/` and `dependencies.py` only when they're needed. Don't add new infrastructure (other databases, queues, external services) without asking.

## Naming

| What                        | Rule                         | Example                                  |
| --------------------------- | ---------------------------- | ---------------------------------------- |
| Modules, packages           | snake_case                   | `routers/blog_posts.py`                  |
| Functions, variables        | snake_case                   | `get_project_by_slug`                    |
| Classes, Pydantic models    | PascalCase                   | `ProjectRead`                            |
| Constants                   | UPPER_SNAKE_CASE             | `MAX_PAGE_SIZE`                          |
| Schemas                     | `<Resource><Purpose>`        | `ProjectCreate`, `ProjectUpdate`, `ProjectRead` |
| URL paths                   | lowercase, kebab-case, plural nouns | `/api/projects`, `/api/blog-posts/{slug}` |
| Models (SQLAlchemy)         | PascalCase, singular         | `User`, `BlogPost` in `models/blog_post.py` |
| Tables (`__tablename__`)    | snake_case, plural           | `users`, `blog_posts`                    |
| Migration messages          | lowercase, imperative        | `"create users table"`, `"add avatar url to users"` |
| Celery task names           | `<area>.<action>`            | `emails.send_contact_message`            |
| Tests                       | `test_<behavior>`            | `test_create_project_rejects_empty_title` |

## API rules

- **Routers per resource.** `router = APIRouter(prefix="/projects", tags=["projects"])` in `routers/projects.py`, included in `main.py` under the `/api` prefix: `app.include_router(projects.router, prefix="/api")`. `/health` stays at the root for uptime checks.
- **Type everything.** mypy runs in strict mode: every function has parameter and return annotations.
- **Declare responses with return types.** Write `async def get_project(...) -> ProjectRead:`. FastAPI uses the return annotation for validation, filtering and OpenAPI. Use `response_model=` only when the returned object differs from the declared type.
- **Use `Annotated` for parameters and dependencies.** `slug: Annotated[str, Path()]`, `settings: Annotated[Settings, Depends(get_settings)]`, not default-value style `= Depends(...)`. Ruff's `FAST` rules flag this.
- **`async def` vs `def`.** Use `async def` only when everything awaited inside is async (httpx, async DB drivers). Code that calls blocking libraries goes in plain `def`, which FastAPI runs in a threadpool. Never block inside `async def` (`time.sleep`, `requests`, sync DB calls). Ruff's `ASYNC` rules flag common cases.
- **Errors.** Raise `HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")`, using `fastapi.status` constants rather than bare numbers.
- **Status codes.** Set them on the decorator for non-200 success: `@router.post("", status_code=status.HTTP_201_CREATED)`.
- **Validate at the edge.** Request bodies and query parameters are Pydantic models or typed parameters with constraints (`Field(min_length=1, max_length=200)`). Don't validate by hand inside the endpoint.
- **Pydantic v2 APIs only.** `model_config = ConfigDict(...)`, `model_dump()`, `model_validate()`, not `class Config`, `.dict()` or `.parse_obj()`.

## Database (SQLAlchemy 2 + Alembic)

- **Typed models only:** `Mapped[...]` + `mapped_column(...)`, inheriting from `app.models.base.Base`. Never `Column(...)` on the class or the legacy `declarative_base()`.
- **Sessions come from the dependency.** Endpoints take `session: SessionDep` and `await session.execute(select(...))`. Never create engines or sessions in routers or services.
- **Async all the way.** The driver is asyncmy, so database calls are awaited inside `async def`. Never call the database from sync code in the API.
- **Lengths on strings.** MariaDB needs them: `String(255)`, not bare `String`. Use `Text` for long content.
- **Every schema change is an Alembic migration.** Autogenerate it, review it, test upgrade + downgrade (workflow in `backend/CLAUDE.md`). Never `Base.metadata.create_all()`, and never edit a merged migration.
- Constraint names come from the naming convention in `models/base.py`. Don't name constraints by hand (`Index(None, "user_id", "expires_at")`).
- **Schema conventions** (enforced by `tests/test_models.py`):
  - Tables inherit InnoDB, utf8mb4 and `utf8mb4_uca1400_ai_ci` from `Base`. A model with its own `__table_args__` must end the tuple with `TABLE_OPTIONS`.
  - Ids are `BIGINT UNSIGNED` via `IdMixin`; foreign key columns use `UnsignedBigInt` to match.
  - Every table except pure association tables uses `TimestampMixin`: `created_at` / `updated_at` set by MariaDB, in UTC (the engine sets the session time zone to `+00:00`). Datetimes are naive UTC in Python: `datetime.now(UTC).replace(tzinfo=None)`.
  - Every foreign key states `ondelete=`: `CASCADE` for rows that only exist with their parent, `SET NULL` for nullable optional links, `RESTRICT` when deletion must be blocked.
  - Booleans and columns with defaults are `NOT NULL` with a `server_default`.
  - Status fields are a `StrEnum` in `app/models/enums.py`, mapped with `status_enum(...)` from `models/base.py` (`VARCHAR(20)` + check constraint `ck_<table>_status`), never a native `ENUM`. Adding a value needs a hand-written migration that drops and re-creates that check constraint; Alembic doesn't detect check constraint changes. No soft deletes: hide rows with an `archived` status.
  - Rules between columns are check constraints with a short name, which the convention prefixes: `CheckConstraint("end_date IS NULL OR end_date >= start_date", name="end_date_after_start")` becomes `ck_experiences_end_date_after_start`.
  - Files live in ImageKit and are rows in `media` (`file_id`, `file_path`, size, dimensions); other tables reference `media.id`, never store a file URL.
  - Relationships use `lazy="raise"` (async can't lazy-load); load them explicitly with `selectinload(...)`.
- **MariaDB reuses an index for a foreign key** when the FK column is its first column. Autogenerated downgrades that drop such an index before its table fail with error 1553; drop the table only.

## Authentication

- Admin-only endpoints take `user: CurrentUserDep` (`app/dependencies.py`): a valid `Authorization: Bearer <access token>` for an active user, otherwise 401 with `WWW-Authenticate: Bearer`. Public endpoints take nothing.
- Access tokens are HS256 JWTs (`JWT_SECRET_KEY`, `ACCESS_TOKEN_EXPIRE_MINUTES`). Refresh tokens are random, stored only as a SHA-256 hash, and rotate on every `POST /auth/refresh`; reusing a rotated one revokes all of that user's tokens.
- Tokens are returned in the JSON body, never set as cookies by the API. The Next.js server keeps them in its own httpOnly cookies and calls the API with the Bearer header.
- Passwords are hashed only through `app/core/security.py` (pwdlib, argon2). Never log passwords or tokens.
- Create the admin with `uv run python -m app.commands.create_admin --email <email>` (add `--reset-password` to change it).

## Redis, Celery and Sentry

- **Redis:** inject `redis: RedisDep` (async client). Always set an expiry on cache keys (`ex=` seconds), and prefix keys by area (`projects:list`).
- **Celery tasks** are plain `def` functions decorated with `@celery_app.task(name="<area>.<action>")` in `app/tasks/<area>.py`, added to `include` in `app/worker.py`. Arguments and results must be JSON-serializable (ids, not ORM objects). Enqueue with `.delay(...)` from the API; never wait for a result inside a request.
- **Sentry** is initialised by `init_sentry()` in `main.py` and `worker.py` and only runs when `SENTRY_DSN` is set. Never send personal data (`send_default_pii=False`).

## Configuration & secrets

- Read configuration only through `Settings` in `app/core/config.py`. Inject it with `Annotated[Settings, Depends(get_settings)]`, never `os.environ` / `os.getenv`.
- **Secrets never go in code or committed files.** Locally they live in `backend/.env` (gitignored, excluded from Docker images). In production (e.g. Vercel) they go in the platform's environment-variable settings. Use `SecretStr` for passwords, keys and tokens.
- Document every variable in `backend/.env.example` with a safe placeholder or the local default, never a real secret.
- CORS origins come from `CORS_ORIGINS`. Never use `allow_origins=["*"]` together with `allow_credentials=True`.

## Dependencies

- Manage packages only with uv: `uv add <pkg>`, `uv add --dev <pkg>`, `uv remove <pkg>`. Never use `pip install`, and never edit `uv.lock` by hand.
- Commit `pyproject.toml` and `uv.lock` together. CI installs with `uv sync --locked` and fails if they don't match.

## Tests

- Every new endpoint gets tests through the shared `client` fixture (`fastapi.testclient.TestClient`) in `tests/conftest.py`.
- Test behavior through HTTP (status code + JSON body), not internals.
- Override dependencies in tests with `app.dependency_overrides`, and reset them after the test.
- Unit tests (`tests/test_*.py`) must not need MariaDB or Redis: override `get_session` / `check_database` / `get_redis`. Redis stand-ins live in `tests/fakes.py`.
- Flows that depend on real SQL (locking, constraints, rotation) go in `tests/integration/`: the `api` fixture (async `httpx.AsyncClient`) and `db_session` run every test in one transaction that is rolled back, so nothing is written. They need the database migrated to head; locally they skip when MariaDB is down, in CI (`TESTS_REQUIRE_DATABASE=1`) they fail instead.
- Async tests use `pytestmark = pytest.mark.anyio` (anyio's plugin, no pytest-asyncio).

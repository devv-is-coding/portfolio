---
paths:
  - 'backend/**'
---

# Backend conventions

## Structure and layers

- `app/routers/` HTTP only (parse, call one service function, return a schema) → `app/services/` business rules, owns the transaction (`commit()`) → `app/repositories/` queries only, never commit (`BaseRepository[Model]`; add a method only when a service needs that query).
- `app/core/`: config, database, redis, security, errors, logging, pagination, slugs, imagekit. `app/schemas/` one module per resource. `app/models/` one module per table, imported in `__init__.py`. `app/commands/` CLI scripts (`python -m app.commands.<name>`).
- Don't add new infrastructure (databases, queues, external services) without asking.

## Naming

- snake_case modules, functions, variables; PascalCase classes; UPPER_SNAKE constants.
- Schemas `<Resource>Create` / `Update` / `Read`. Models singular (`BlogPost`), tables plural snake_case (`blog_posts`). URL paths plural kebab-case.
- Migration messages lowercase imperative (`"add avatar url to users"`). Celery tasks `<area>.<action>`. Tests `test_<behavior>`.

## API

- Public reads at `/<resource>`; admin routes at `/admin/<resource>`, every one behind `CurrentUserDep` / `AuditContextDep` / router-level `get_current_user` (`tests/test_route_protection.py` enforces it). `/health` and `/auth` at the root.
- Strict typing everywhere; responses declared by return type; `Annotated[...]` for parameters and dependencies.
- `async def` only when everything awaited is async; never block inside it.
- Validate at the edge with Pydantic constraints that match the column limits. Pydantic v2 APIs only.
- Errors: services raise `AppError` subclasses from `app/core/errors.py` (`NotFoundError`, `ConflictError`, `UnauthorizedError`, `ValidationFailedError`, `RateLimitedError`, `UpstreamError`, `ServiceUnavailableError`); never `HTTPException`. One shape: `{"error": {"code", "message", "details"}}`. Document with `responses=error_responses(...)`, including 422 on routers with inputs.
- Lists: `PageParamsDep`, `sort_query(...)` allowlist, `SearchQuery`; return `Page[<Name>Read]`. Repositories use `apply_sort(..., Model.id)`, `search_filter(...)` and `paginate(...)`.
- Slugs: `Slug` type + `slugify()`; duplicates are 409 from the unique index.
- Audit every admin create/update/delete and security event with `audit.record(...)` in the same transaction; details are the changes (`audit.changes(...)`), never request bodies.
- Logging: `logging.getLogger(__name__)`; never log passwords, tokens, headers, bodies or query strings. Client IP only via `ClientIpDep`.
- Config only through `Settings` (`SettingsDep`), never `os.environ`. Secrets as `SecretStr`. Never `allow_origins=["*"]` with credentials.

## Database

- Typed models (`Mapped` + `mapped_column`) on `Base`; string columns need lengths; async calls only.
- Tables inherit `TABLE_OPTIONS` (models with their own `__table_args__` end with it); `IdMixin`, `TimestampMixin` (naive UTC); FK columns `UnsignedBigInt` with explicit `ondelete=`. `tests/test_models.py` enforces these.
- Don't name constraints by hand (naming convention), except check constraints get a short `name=`.
- Status fields: `StrEnum` in `app/models/enums.py` via `status_enum(...)`, never native `ENUM`; adding a value needs a hand-written migration. No soft deletes (`archived`).
- Relationships `lazy="raise"`; load with `selectinload(...)`.
- Files are `media` rows (ImageKit); reference `media.id`, never store URLs. All ImageKit calls go through `ImageKitClient`; tests use `FakeImageKit`, never the real ImageKit.
- An index whose first column is an FK backs that FK in MariaDB: in downgrades drop the table, not the index (error 1553).

## Auth

- Admin endpoints need a Bearer access token (HS256 JWT). Refresh tokens rotate and are stored hashed; reuse revokes all. The API never sets cookies.
- Hash passwords only via `app/core/security.py`. Admin account: `uv run python -m app.commands.create_admin --email <email> [--reset-password]`.

## Dependencies

- Only uv: `uv add` / `uv add --dev` / `uv remove`; never pip, never edit `uv.lock` by hand. Commit `pyproject.toml` with `uv.lock`.

## Tests

- Behaviour through HTTP (status + body). Reset `app.dependency_overrides` after each test.
- Unit tests (`tests/test_*.py`) need no MariaDB or Redis; stand-ins and `IsolatedSettings` live in `tests/fakes.py` (never `Settings()` in tests: it reads `.env`).
- Real-SQL flows go in `tests/integration/` (`api`, `db_session`, `admin`, `admin_headers` fixtures; each test rolled back). Async tests: `pytestmark = pytest.mark.anyio`.
- Admin endpoint tests cover success, 404, 409, 422, filters/pagination and the audit entry (401 is covered by the route-protection test).

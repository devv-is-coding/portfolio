---
paths:
  - 'backend/**'
---

<!--
  Backend (FastAPI) rules. Claude Code must follow these when working in backend/.
  Loaded by backend/CLAUDE.md. Enforced by ruff, mypy (strict), pytest and CI.
-->

# Backend conventions (FastAPI)

Python 3.13, FastAPI, Pydantic v2, pydantic-settings, managed with **uv**. All paths below are relative to `backend/`. Run everything from `backend/`:

```bash
uv run fastapi dev                 # dev server with reload (entrypoint set in pyproject.toml)
uv run ruff check . --fix          # lint (+ autofix)
uv run ruff format .               # format
uv run mypy app tests              # type check (strict)
uv run pytest                      # tests
```

CI (`.github/workflows/ci.yml`, job **Backend**) runs `ruff check`, `ruff format --check`, `mypy` and `pytest` on every push and pull request. Fix every failure before finishing a task.

## Folder structure

```
app/
  main.py          Creates the FastAPI app: middleware, CORS, include_router(...). No endpoints here.
  core/config.py   Settings (pydantic-settings) + get_settings()
  dependencies.py  Shared dependencies (auth, DB session, ...) when needed
  routers/         One APIRouter per resource: projects.py, contact.py, health.py
  schemas/         Pydantic request/response models, one module per resource
  services/        Business logic; routers stay thin and call services
tests/
  conftest.py      Shared fixtures (TestClient, ...)
  test_<module>.py Tests, mirroring app/ (routers/test_projects.py for larger suites)
```

Add `services/`, `dependencies.py`, `models/` (database) only when they're needed. Don't add a database, auth or other infrastructure without asking.

## Naming

| What                        | Rule                         | Example                                  |
| --------------------------- | ---------------------------- | ---------------------------------------- |
| Modules, packages           | snake_case                   | `routers/blog_posts.py`                  |
| Functions, variables        | snake_case                   | `get_project_by_slug`                    |
| Classes, Pydantic models    | PascalCase                   | `ProjectRead`                            |
| Constants                   | UPPER_SNAKE_CASE             | `MAX_PAGE_SIZE`                          |
| Schemas                     | `<Resource><Purpose>`        | `ProjectCreate`, `ProjectUpdate`, `ProjectRead` |
| URL paths                   | lowercase, kebab-case, plural nouns | `/api/projects`, `/api/blog-posts/{slug}` |
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

## Configuration & secrets

- Read configuration only through `Settings` in `app/core/config.py`. Inject it with `Annotated[Settings, Depends(get_settings)]`, never `os.environ` / `os.getenv`.
- Secrets go in `backend/.env` (gitignored). Document every variable in `backend/.env.example`.
- CORS origins come from `CORS_ORIGINS`. Never use `allow_origins=["*"]` together with `allow_credentials=True`.

## Dependencies

- Manage packages only with uv: `uv add <pkg>`, `uv add --dev <pkg>`, `uv remove <pkg>`. Never use `pip install`, and never edit `uv.lock` by hand.
- Commit `pyproject.toml` and `uv.lock` together. CI installs with `uv sync --locked` and fails if they don't match.

## Tests

- Every new endpoint gets tests through the shared `client` fixture (`fastapi.testclient.TestClient`) in `tests/conftest.py`.
- Test behavior through HTTP (status code + JSON body), not internals.
- Override dependencies in tests with `app.dependency_overrides`, and reset them after the test.

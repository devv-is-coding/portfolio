# Portfolio

Personal portfolio: a Next.js frontend and a FastAPI backend in one repository.

| Folder                   | What                                                    | Get started                                   |
| ------------------------ | ------------------------------------------------------- | --------------------------------------------- |
| [`frontend/`](frontend/) | Next.js 16, React 19, TypeScript, Tailwind v4, GSAP / Motion | `cd frontend && npm install && npm run dev`   |
| [`backend/`](backend/)   | FastAPI, Python 3.13, managed with [uv](https://docs.astral.sh/uv/) | `cd backend && uv sync && uv run fastapi dev` |

- Frontend: http://localhost:3000
- Backend: http://localhost:8000 (interactive API docs at `/docs`)

## Docker

Needs Docker Desktop. Run from the repo root:

```bash
docker compose up --watch                        # dev stack: next dev :3000 + fastapi dev :8000, host edits synced in
docker compose -f compose.prod.yaml up --build   # production images
```

## Checks

```bash
cd frontend && npm run check                                   # conventions, lint, types
cd backend && uv run ruff check . && uv run mypy app tests && uv run pytest
```

CI (`.github/workflows/ci.yml`) runs the frontend checks, the backend checks, a Docker build + smoke test, and the commit-message check ([Conventional Commits](https://www.conventionalcommits.org)) on every push and pull request.

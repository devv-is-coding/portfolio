# Portfolio

Monorepo: Next.js 16 frontend (`frontend/`) + FastAPI backend (`backend/`). The two apps never import from each other; they talk only over HTTP. Before changing either app, read its `CLAUDE.md`. Run commands from the app's folder (Docker and Git from the repo root).

## Rules files

- Never add, extend or reword any CLAUDE.md or `.ai/rules/*.md` unless the user asks for that change. Propose short wording and wait for approval. Keep them short: they load into every session.
- `.ai/rules/github.md`: read before any commit, branch, push or PR.

## Plan

- `TODO.md` (gitignored) is the plan. Start every task from it; after each verified task, tick it, add follow-ups and a dated log entry. `backend/progress.md` / `frontend/progress.md` (gitignored) get a dated log entry too.
- Backend first: no frontend feature work until every backend completion requirement in `TODO.md` is ticked with evidence. One verified task per session; never mark a task done without verification.

## Secrets

- Secrets only in env vars: `backend/.env`, `frontend/.env.local` (gitignored, never in Docker images); on Vercel in Project → Settings → Environment Variables.
- Never commit or hardcode a secret, never put one in `.env.example` (placeholders only), never give one a `NEXT_PUBLIC_` prefix. Every new variable goes into the matching `.env.example`.

## Checks: resolve every error before ending a task

- Frontend (`frontend/`): `npm run check`. Backend: see `backend/CLAUDE.md`.
- Every error catcher must be clean: lint, format, types, tests, builds, `alembic check`, the editor's diagnostics for touched files, and errors in command output and container logs. Fix the cause; never silence with `# type: ignore`, `# noqa`, `eslint-disable`, `@ts-expect-error`, skipped tests or looser config. If something can't be fixed, report it with the exact output.

## Docker

- Dev stack: `docker compose up --watch` (frontend :3000, backend :8000, worker, mariadb host :3307, redis host :6380, `migrate` runs `alembic upgrade head` on every up). No bind mounts: watch syncs host → container one way.
- Run installs and generators on the host (`npm install`, `uv add`), never via `docker compose exec`.
- `.env` files are read only at container creation: after changing one, `docker compose up -d --force-recreate <service>`, then restart `docker compose up --watch` (a recreate resets the container's source).
- Git Bash: prefix `docker compose exec` with `MSYS_NO_PATHCONV=1`.
- Before ending a task that changed files: make sure watch is running and confirm the containers have the change (file content under `/app`, new routes respond, new endpoints are in `/openapi.json`).
- A new dependency, env var, port or build step updates both Dockerfile stages, `compose.yaml`, `compose.prod.yaml` and `.env.example` together. `NEXT_PUBLIC_*` vars are build `args` in `compose.prod.yaml`.
- Browser → `NEXT_PUBLIC_API_URL` (`http://localhost:8000`); Next.js server → `API_URL` (`http://backend:8000`). Never hardcode either.
- Containers run as non-root. Never run `docker compose down -v` (deletes the database) without explicit permission.

## Git

- **Never commit unless the user explicitly says so** ("commit", "push it"), local commits included. Never commit to `main` directly.
- Conventional Commits, lowercase, imperative, title under 72 characters, and a detailed body. Branches `<type>/<1-4-words>`. Details in `.ai/rules/github.md`.
- One commit per task (e.g. `B4`, `B12`): never bundle several tasks into one commit.
- Before every push, run CI locally and push only when all pass:
  - `frontend/`: `npm run check && npm run build`
  - `backend/`: the checks in `backend/CLAUDE.md`, plus `uv run alembic check`
  - repo root: `npx commitlint --from origin/main --to HEAD`, and the PR title: `echo "<title>" | npx commitlint --config commitlint.title.config.mjs`
  - workflows changed: `uv run --no-project --with actionlint-py actionlint`
  - Dockerfile/compose changed: `docker build --target dev ./frontend`, `docker build --target dev ./backend`, then `docker compose -f compose.prod.yaml up --build -d --wait`, curl `:8000/health` and `:3000`, then `down`.
- Push one branch at a time, all its commits in one `git push -u origin <branch>`. Start the next branch only after it's merged.
- Never switch branches over uncommitted changes, discard user changes, or run destructive Git operations without explicit permission.

@TODO.md

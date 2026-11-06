# Portfolio

Monorepo for a personal portfolio: a **Next.js 16** frontend and a **FastAPI** backend in one repository.

## Editing CLAUDE.md files

**Do not edit any CLAUDE.md (this one, `frontend/CLAUDE.md`, `backend/CLAUDE.md`) on your own initiative.** Change one only when the user explicitly asks you to, or when a change is truly necessary for it to stay correct (for example, a command or path it documents was renamed or removed). In that case, tell the user what you changed and why. Never add notes, learnings, or rewording casually.

## Repository layout

```
frontend/            Next.js 16 app (App Router, React 19, TypeScript, Tailwind v4, GSAP / Motion)
backend/             FastAPI API (Python 3.13, uv, Pydantic v2)
TODO.md              Development plan and task checklist (gitignored, local only; see **TODO.md**)
.ai/rules/           Rules for Claude: frontend.md, backend.md, github.md
.github/workflows/   ci.yml: frontend, backend, Docker, branch-name and commit-message checks on every push and PR
.claude/skills/      Project-local skills (gsap-scrolltrigger, modern-web-design, …)
compose.yaml         Docker dev stack: next dev + fastapi dev with watch sync (see **Docker**)
compose.prod.yaml    Docker production images (used by CI's smoke test)
package.json         Repo-level tooling only (commitlint). Not the app.
commitlint.config.mjs        Commit message rules (commitlint.title.config.mjs: same rules for PR titles, no body)
```

**Before creating or changing anything in `frontend/` or `backend/`, read that folder's `CLAUDE.md`.** It loads the rules for that part. Run commands from inside the folder they belong to, and keep the two apps independent: no imports across the boundary. They talk only over HTTP.

## TODO.md

`TODO.md` at the repo root (gitignored, local only) is the development plan: the backend-first strategy, the quality bar, the Phase 1 backend tasks, the **Backend completion requirements**, Phases 2 and 3, blockers and decisions. Start every task from it.

- **Backend first.** No frontend feature work (pages, components, API calls) starts until every backend completion requirement in `TODO.md` is ticked with evidence. The frontend consumes the FastAPI endpoints and never re-implements backend business logic.
- **One meaningful, verified task per session.** Never skip prerequisites, and never mark a task complete without verification.
- **After each verified task, update `TODO.md`:** tick the item, add follow-ups, record new blockers and technical decisions, and add a dated **Log** entry (newest first).

@TODO.md

## Progress notes

`frontend/progress.md` and `backend/progress.md` (both gitignored, local only) keep the detailed technical log of each part: what was built, fixed and verified. Add a dated entry there too when a task in that part is finished.

## Secrets and environment variables

The app will be deployed on Vercel, so all confidential values come from environment variables:
- **Locally:** `backend/.env` and `frontend/.env.local` (both gitignored and kept out of Docker images). Create them from the `.env.example` next to them.
- **On Vercel:** Project → Settings → Environment Variables, with the same names. `vercel env pull .env.local` downloads them for the frontend.
- Never commit secrets, never hardcode them, and never put them in a `.env.example`. Every new variable goes into the matching `.env.example` with a placeholder or the local default.
- Never give a secret the `NEXT_PUBLIC_` prefix: those values end up in the browser bundle.

## Project rules

- `.ai/rules/frontend.md`: Next.js naming, Server/Client components, imports, lint. Loaded by `frontend/CLAUDE.md`.
- `.ai/rules/backend.md`: FastAPI structure, naming, typing, settings, uv, tests. Loaded by `backend/CLAUDE.md`.
- `.ai/rules/github.md`: commit messages, branch names, branch workflow and cleanup. Read it before any Git action (see **Git**).

## Commands

The dev stack normally runs in Docker (`docker compose up --watch`, see **Docker**). Checks and tests run on the host:

| Part     | Run from    | Native dev server (without Docker) | Before finishing a task                                  |
| -------- | ----------- | ---------------------------------- | -------------------------------------------------------- |
| Frontend | `frontend/` | `npm run dev` (:3000)              | `npm run check`                                          |
| Backend  | `backend/`  | `uv run fastapi dev` (:8000)       | `uv run ruff check . && uv run ruff format --check . && uv run mypy app tests alembic && uv run pytest` |

Always run the checks for every part you changed, and fix every failure before reporting the task as done. CI runs the same checks, so a local warning becomes a CI failure.

**Resolve every error before ending a task.** That covers everything that catches errors: lint (ruff, ESLint), format, type checks (mypy, `tsc`), tests, builds, migrations (`alembic check`), the editor's diagnostics for the files you touched, and errors or warnings in command output and container logs. Fix the cause. Don't silence it with `# type: ignore`, `# noqa`, `eslint-disable`, `@ts-expect-error`, skipped tests or loosened config unless there's no other way, and then say why in a comment and in your report. If an error can't be fixed within the task, don't end silently: report it, with the exact output.

## Docker (Local Development)

`compose.yaml` runs the dev stack: `frontend` (`next dev`, :3000), `backend` (`fastapi dev`, :8000), `worker` (Celery), `mariadb` (MariaDB 11.8, host port 3307, data in the `mariadb-data` volume), `redis` (host port 6380), and `migrate`, a one-shot job that runs `alembic upgrade head` on every `up` before the backend and worker start. `compose.prod.yaml` runs the production images (`output: "standalone"` Next.js server, `fastapi run`), which CI's **Docker** job builds and smoke-tests. Run Docker commands from the repo root.

```bash
docker compose up --watch                          # dev stack + sync host edits into the containers
docker compose up -d --force-recreate backend worker  # after changing backend/.env (frontend/.env.local: recreate frontend)
docker compose logs -f backend                     # follow one service's logs
docker compose down                                # stop and remove the containers
docker compose -f compose.prod.yaml up --build     # production images, locally
```

- The source is not bind-mounted, because bind mounts from the Windows drive are slow. Start the stack with `docker compose up --watch`, which syncs host edits into the containers.
- Sync is one-way, host to container. Run dependency changes and file generators on the host (`npm install <pkg>` in `frontend/`, `uv add <pkg>` in `backend/`, any `npx … add` / scaffolding command), never through `docker compose exec`. Anything created inside a container is never copied back to the host.
- Changes to `frontend/package.json` / `package-lock.json` or `backend/pyproject.toml` / `uv.lock` rebuild that service's image automatically while watch is running.
- `.env` files are read only when the container is created: `backend/.env`, and `frontend/.env.local` (both optional). After changing one, run `docker compose up -d --force-recreate <service>`.
- Recreating or restarting a container resets its source to the image's copy and detaches the running watch. Every edit since the last image build disappears *inside the container*: new pages 404, new endpoints vanish. Nothing is lost on the host. Always follow a recreate with `docker compose up --watch` (its `initial_sync` re-copies the host source), then confirm the work is back before reporting anything as broken.
- From Git Bash on Windows, prefix `docker compose exec` with `MSYS_NO_PATHCONV=1`. Otherwise container paths like `/app/...` are rewritten into Windows paths and the command fails.
- **Before ending any task that changed files, update the running containers.** Make sure `docker compose up --watch` is running (start it in the background if it isn't), then confirm the containers have the work:
  - A changed file's content matches inside `docker compose exec -T frontend` / `docker compose exec -T backend` (files live under `/app`).
  - A new page responds at `http://localhost:3000/<route>`, and a new endpoint responds at `http://localhost:8000/...` and is listed in `http://localhost:8000/openapi.json`.

  Checks and tests pass on the host without the containers, so they don't prove the app the user sees is current.
- **Keep Docker in sync with the apps.** When you add a dependency, env var, port or build step, update the matching Dockerfile (both the `dev` and production stages), `compose.yaml`, `compose.prod.yaml` and `.env.example` in the same change.
- **`NEXT_PUBLIC_*` variables:** in `compose.yaml` (`next dev`) they're plain `environment` entries. In `compose.prod.yaml` they must be build `args`, because `next build` inlines them into the browser bundle. Server-only variables (like `API_URL`) are runtime `environment` in both.
- **Two backend URLs.** The browser calls `NEXT_PUBLIC_API_URL` (`http://localhost:8000`). Server-side Next.js code inside the container calls `API_URL` (`http://backend:8000`, the Compose service name). Never hardcode either.
- **Standalone output is Docker-only.** `next.config.ts` enables it only when `NEXT_OUTPUT=standalone`, which the production Dockerfile stage sets. Leave it unset elsewhere so Vercel builds keep working.
- Containers run as non-root users (`node`, `app`). Keep it that way, and never copy `.env` files or secrets into an image.
- `docker compose down` keeps the database (the `mariadb-data` volume). `docker compose down -v` deletes it; never run that without the user's explicit permission.
- Don't change the pinned uv image (`UV_VERSION` in `backend/Dockerfile`) or the Node/Python base versions casually. Bump them together with CI and local tooling.

## Git

- Before any commit, branch, push or pull request, read `.ai/rules/github.md` (commit message types and rules, branch names, branch workflow and cleanup). No file edit triggers it, so this line is its trigger.
- The ones never to miss:
  - Commit only when the user explicitly asks or the task requires it, as Conventional Commits: `<type>(<scope>): <short description>`, lowercase, imperative, under 72 characters. The title names what changed in detail, and **every commit has a detailed body**: one paragraph per task, covering what was built, how it behaves and key decisions (format and example in `.ai/rules/github.md`). Branch names stay short (1–4 words); the detail goes in the commits.
  - Never commit directly to `main` unless the user or the established workflow explicitly permits it.
  - **Before every push, run the CI checks locally and push only when all of them pass.** If one fails, fix it first. Never push to "see if CI passes".
    - Frontend, from `frontend/`: `npm run check && npm run build`
    - Backend, from `backend/`: `uv run ruff check . && uv run ruff format --check . && uv run mypy app tests alembic && uv run pytest`, then `uv run alembic check` (needs the Docker MariaDB running)
    - Commit messages, from the repo root: `npx commitlint --from origin/main --to HEAD`. Also check the PR title you'll use: `echo "<title>" | npx commitlint --config commitlint.title.config.mjs`.
    - Branch name: matches the branch types in `.ai/rules/github.md` (`feature/`, `fix/`, `hotfix/`, `refactor/`, `docs/`, `test/`, `chore/`, `style/`, `perf/`), 1–4 words.
    - If `.github/workflows/` changed: `uv run --no-project --with actionlint-py actionlint`
    - If a Dockerfile, `.dockerignore` or compose file changed: `docker build --target dev ./frontend`, `docker build --target dev ./backend`, then `docker compose -f compose.prod.yaml up --build -d --wait`, `curl -f http://localhost:8000/health`, `curl -f http://localhost:3000`, and `docker compose -f compose.prod.yaml down`
  - **Push one branch at a time.** Put all commits for the current work on a single branch and push them together with one command (`git push -u origin <branch>`). Keep separate topics apart with separate commits on that branch, not with extra branches. Never push several branches in one go or stack a new branch on top of an unmerged one. Start the next branch only after the current one is merged into `main`, or when the user explicitly asks.
  - Never switch branches over uncommitted user changes, discard user changes, or run destructive Git operations without explicit authorization.

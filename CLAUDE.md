# Portfolio

Monorepo for a personal portfolio: a **Next.js 16** frontend and a **FastAPI** backend in one repository.

## Editing CLAUDE.md files

**Do not edit any CLAUDE.md (this one, `frontend/CLAUDE.md`, `backend/CLAUDE.md`) on your own initiative.** Change one only when the user explicitly asks you to, or when a change is truly necessary for it to stay correct (for example, a command or path it documents was renamed or removed). In that case, tell the user what you changed and why. Never add notes, learnings, or rewording casually.

## Repository layout

```
frontend/            Next.js 16 app (App Router, React 19, TypeScript, Tailwind v4, GSAP / Motion)
backend/             FastAPI API (Python 3.13, uv, Pydantic v2)
.ai/rules/           Rules for Claude: frontend.md, backend.md, github.md
.github/workflows/   ci.yml: frontend, backend, Docker, branch-name and commit-message checks on every push and PR
.claude/skills/      Project-local skills (gsap-scrolltrigger, modern-web-design, …)
compose.yaml         Docker dev stack: next dev + fastapi dev with watch sync (see **Docker**)
compose.prod.yaml    Docker production images (used by CI's smoke test)
package.json         Repo-level tooling only (commitlint). Not the app.
commitlint.config.mjs
```

**Before creating or changing anything in `frontend/` or `backend/`, read that folder's `CLAUDE.md`.** It loads the rules for that part. Run commands from inside the folder they belong to, and keep the two apps independent: no imports across the boundary. They talk only over HTTP.

## Project rules

- `.ai/rules/frontend.md`: Next.js naming, Server/Client components, imports, lint. Loaded by `frontend/CLAUDE.md`.
- `.ai/rules/backend.md`: FastAPI structure, naming, typing, settings, uv, tests. Loaded by `backend/CLAUDE.md`.
- `.ai/rules/github.md`: commit messages, branch names, branch workflow and cleanup. Read it before any Git action (see **Git**).

## Commands

The dev stack normally runs in Docker (`docker compose up --watch`, see **Docker**). Checks and tests run on the host:

| Part     | Run from    | Native dev server (without Docker) | Before finishing a task                                  |
| -------- | ----------- | ---------------------------------- | -------------------------------------------------------- |
| Frontend | `frontend/` | `npm run dev` (:3000)              | `npm run check`                                          |
| Backend  | `backend/`  | `uv run fastapi dev` (:8000)       | `uv run ruff check . && uv run ruff format --check . && uv run mypy app tests && uv run pytest` |

Always run the checks for every part you changed, and fix every failure before reporting the task as done. CI runs the same checks, so a local warning becomes a CI failure.

## Docker (Local Development)

`compose.yaml` runs the dev stack: `frontend` (`next dev`, :3000) and `backend` (`fastapi dev`, :8000). `compose.prod.yaml` runs the production images (`output: "standalone"` Next.js server, `fastapi run`), which CI's **Docker** job builds and smoke-tests. Run Docker commands from the repo root.

```bash
docker compose up --watch                          # dev stack + sync host edits into the containers
docker compose up -d --force-recreate backend      # after changing backend/.env (or frontend/.env.local for frontend)
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
- Don't change the pinned uv image (`UV_VERSION` in `backend/Dockerfile`) or the Node/Python base versions casually. Bump them together with CI and local tooling.

## Git

- Before any commit, branch, push or pull request, read `.ai/rules/github.md` (commit message types and rules, branch names, branch workflow and cleanup). No file edit triggers it, so this line is its trigger.
- The ones never to miss:
  - Commit only when the user explicitly asks or the task requires it, as Conventional Commits: `<type>(<scope>): <short description>`, lowercase, imperative, under 72 characters.
  - **Never commit to `main`.** Always work on a sub-branch created from an up-to-date `main`, and get changes into `main` through a pull request.
  - **Name sub-branches with the same types as commits:** `<type>/<short-description>`, e.g. `feat/hero-section`, `fix/42-nav-overflow`, `chore/bump-next`, `docs/docker-setup`. Types: `feat`, `fix`, `refactor`, `style`, `docs`, `test`, `perf`, `build`, `ci`, `chore`, `revert`.
  - **Keep local branches few.** Before creating a new sub-branch, update `main`. Once `main` contains a merged sub-branch and a second merged one exists, delete the older one, so only the most recently merged sub-branch stays as a rollback point. Squash-merged branches show as `[gone]` in `git branch -vv`; the exact steps are in `.ai/rules/github.md`.
  - Never switch branches over uncommitted user changes, discard user changes, or run destructive Git operations without explicit authorization.
- Use the part as the scope when a change touches only one: `feat(frontend): …`, `fix(backend): …`, `ci: …`.

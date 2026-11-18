# Portfolio frontend

Next.js 16 (App Router, Cache Components), React 19, TypeScript and Tailwind CSS v4. It talks to the FastAPI backend (`../backend`) over HTTP only.

## Commands

Run from `frontend/`:

| Command | What it does |
|---|---|
| `npm run dev` | Development server on http://localhost:3000 (in Docker: `docker compose up --watch` from the repo root) |
| `npm run check` | Conventions, ESLint, TypeScript and unit tests (run before every commit) |
| `npm test` | Unit tests (Vitest), e.g. `npm test -- lib/api` |
| `npm run api:types` | Regenerate `lib/api/schema.ts` from the running backend's `/openapi.json` (after an API change) |
| `npm run build` | Production build |
| `npm run check:budgets` | Lighthouse CI on the production build (run `npm run build` first) |

## Environment

Copy `.env.example` to `.env.local`. `NEXT_PUBLIC_API_URL` is the backend URL for the browser; `API_URL` is the backend URL for server code (`http://backend:8000` in Docker). Never give a secret the `NEXT_PUBLIC_` prefix.

## Talking to the API

Only server code calls the FastAPI backend, through `apiClient()` in `lib/api/client.ts` (`API_URL`). The browser never does: admin tokens live in httpOnly cookies on the Next.js server, and forms post to Server Actions. Paths, parameters and bodies are typed from the generated `lib/api/schema.ts`.

- `unwrap(apiClient().GET("/skills"))` returns the data or throws an `ApiError` (`status`, `code`, `message`, `fieldErrors()` for forms). When the API can't be reached at all it throws `api_unreachable` (503).
- `apiClient({ accessToken, clientIp })` adds `Authorization: Bearer ...` and `X-Forwarded-For`, so the API's per-IP limits see the visitor.
- Cached public reads tag themselves with one of `CACHE_TAGS` (`lib/api/cache-tags.ts`); admin writes call `updateTag` for the tags they affect.

## Admin sign-in

The admin lives under `/admin` (`app/admin/`), never indexed. Create the account in the backend (`create_admin`, see `backend/README.md`), then sign in at `/admin/login`.

- **Tokens stay on the server.** The login Server Action (`lib/auth/actions.ts`) stores the API's access and refresh tokens in httpOnly, SameSite=Lax cookies (`pf_access`, `pf_refresh`; `Secure` in production). Browser JavaScript never sees them.
- **`proxy.ts`** guards `/admin/*`: no session sends the visitor to `/admin/login?next=...`, and an access token within 60 seconds of expiry is refreshed there, before the page renders. The API rotates refresh tokens and treats a second use as theft, so `lib/auth/refresh.ts` refreshes each token only once per server process (parallel requests share the answer for 30 seconds).
- **Every admin read and Server Action checks the session itself** through `asAdmin()` (`lib/auth/session.ts`); a 401 from the API sends the visitor to the login page.
- **Visitor IP:** calls forward the last `X-Forwarded-For` entry (written by the proxy in front of this server) so the API's login limit counts per visitor. The API must trust this server for that (`FORWARDED_ALLOW_IPS` in `backend/.env.example`); without a proxy (local Docker) every login counts as this server's IP.

## Design system

The tokens live in `app/globals.css` (`@theme`). The default Tailwind palette is removed, so only these colors exist:

| Token | Use |
|---|---|
| `ink`, `ink-raised` | Page background, raised surfaces |
| `line` | Borders and dividers |
| `paper`, `muted` | Main and secondary text |
| `accent`, `accent-ink` | Brand lime and the text on it |
| `signal` | Second accent, used sparingly |

Type: `font-display` (Bricolage Grotesque) for headlines with the fluid `text-display` / `text-headline` sizes, `font-sans` (Geist) for body text, `font-mono` (system monospace) for small labels. Motion: `animate-rise` and `animate-marquee`, both off under `prefers-reduced-motion`.

Shared components live in `components/` (`site-header`, `site-footer`, `mobile-nav`, `color-bends`) and `components/ui/` (`container`, `button-link`, `eyebrow`, `marquee`).

`ColorBends` (the hero background) is React Bits' ColorBends shader in plain WebGL (`lib/color-bends-webgl.ts`), without three.js. Its colors are theme variables (`--color-accent`, `--color-signal`). The WebGL code downloads on the visitor's first interaction (pointer, touch, scroll or key), so page load is unaffected; it renders at half resolution and 30 fps, pauses off screen, and draws one still frame under reduced motion.

## Performance budgets

`lighthouserc.json` runs Lighthouse 3 times (mobile profile) and fails CI when the median misses a budget:

- Performance score ≥ 0.95
- LCP < 2.5 s
- CLS < 0.1
- Total blocking time < 200 ms (the lab stand-in for INP)
- JavaScript ≤ 160 KB transferred per page

Add each new main page to `collect.url`. The check serves the build on port 3210, so it doesn't clash with the dev server on 3000. Reports go to `.lighthouseci/` (gitignored).

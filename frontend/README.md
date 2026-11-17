# Portfolio frontend

Next.js 16 (App Router, Cache Components), React 19, TypeScript and Tailwind CSS v4. It talks to the FastAPI backend (`../backend`) over HTTP only.

## Commands

Run from `frontend/`:

| Command | What it does |
|---|---|
| `npm run dev` | Development server on http://localhost:3000 (in Docker: `docker compose up --watch` from the repo root) |
| `npm run check` | Conventions, ESLint and TypeScript (run before every commit) |
| `npm run build` | Production build |
| `npm run check:budgets` | Lighthouse CI on the production build (run `npm run build` first) |

## Environment

Copy `.env.example` to `.env.local`. `NEXT_PUBLIC_API_URL` is the backend URL for the browser; `API_URL` is the backend URL for server code (`http://backend:8000` in Docker). Never give a secret the `NEXT_PUBLIC_` prefix.

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

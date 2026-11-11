# Frontend (Next.js)

Next.js 16 (App Router), React 19, TypeScript, Tailwind v4, GSAP / Motion. Run everything from `frontend/`. Never import from `../backend`; call it over HTTP.

- **This is not the Next.js you know:** read the relevant guide in `node_modules/next/dist/docs/` before writing code, and heed deprecations.
- Before ending a task: `npm run check` (conventions + lint + typecheck; CI adds `next build` and fails on warnings).
- Keep `turbopack.root` and `outputFileTracingRoot` in `next.config.ts` pinned to `frontend/`.
- Use the project skills in `.claude/skills/` for animation and design work.

@../.ai/rules/frontend.md

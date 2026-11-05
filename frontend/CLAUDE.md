# Frontend (Next.js)

Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS v4, GSAP / Motion. Run every command from `frontend/`.

## This is NOT the Next.js you know

This version has breaking changes: APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `frontend/node_modules/next/dist/docs/` before writing any code. Heed deprecation notices.

## Commands

```bash
npm run dev                # dev server (Turbopack), http://localhost:3000
npm run build              # production build (does NOT lint in Next 16)
npm run check              # conventions + lint + typecheck — run before finishing any task
npm run check:conventions  # file/folder/code convention checker only
npm run lint               # ESLint CLI (`next lint` was removed in Next 16)
npm run typecheck          # next typegen && tsc --noEmit
```

CI runs the same checks with `--max-warnings=0` plus `next build`, so a local warning becomes a CI failure.

## Conventions

@../.ai/rules/frontend.md

## Working notes

- Every file and folder name is kebab-case (`components/hero-section.tsx`). Component names inside the file are PascalCase (`export function HeroSection()`).
- `app/` holds Next.js special files only. Shared code goes in `components/`, `hooks/`, and `lib/`. Route-specific code goes in private folders (`app/<route>/_components/`).
- Use the `@/` import alias (e.g. `@/components/hero-section`), never `../../`.
- Keep `app/page.tsx` and `app/layout.tsx` as Server Components. Put `"use client"` only on the interactive leaf components that need it (animation, state, event handlers) and import them into the page.
- Animation code (GSAP, `useGSAP`, `motion/react`) is client-only. With GSAP in React, use `useGSAP()` from `@gsap/react` (it handles cleanup and scoping) instead of raw `useEffect`, and register plugins once (`gsap.registerPlugin(ScrollTrigger, useGSAP)`).
- Respect `prefers-reduced-motion` for any non-essential animation.
- Use `next/image` for images, `next/link` for internal links, and `next/font` for fonts.
- The backend runs at `http://localhost:8000` in development. Never import from `../backend`; call it over HTTP.
- `next.config.ts` pins `turbopack.root` and `outputFileTracingRoot` to `frontend/` because the repo root has its own `package-lock.json`. Keep them.
- Project-local skills live in `.claude/skills/` at the repo root (gsap-scrolltrigger, modern-web-design, scroll-reveal-libraries, …). Use them for animation and design work.

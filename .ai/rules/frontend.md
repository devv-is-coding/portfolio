---
paths:
  - 'frontend/**'
---

# Frontend conventions (enforced by `npm run check`)

- Every file and folder is kebab-case (`components/project-card.tsx` → `export function ProjectCard()`); hooks `hooks/use-<name>.ts` export `use<Name>`. Root config files are exempt.
- `app/` holds routes and Next.js special files only (page, layout, loading, error, route, metadata files, `globals.css`, `*.module.css`). Other route code goes in private folders (`_components/`, `_lib/`); shared code in `components/`, `hooks/`, `lib/`.
- Imports use `@/`, never `../../`. Named exports for shared components; `export default` only where Next.js requires it.
- Server Components by default; `"use client"` only on interactive leaf components (hooks, events, browser globals, GSAP, Motion), as the first statement. `error.tsx` / `global-error.tsx` are client components; `server-only` modules never are.
- `proxy.ts`, not the deprecated `middleware.ts`.
- GSAP in React via `useGSAP()` from `@gsap/react`, plugins registered once; respect `prefers-reduced-motion`.
- `next/image`, `next/link`, `next/font`.
- Lint: no `console.log`, `===`, `const`, `import { type X }`, no unused variables (prefix `_` to keep one), self-closing empty JSX.

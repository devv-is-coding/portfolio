---
paths:
  - 'frontend/**'
---

<!--
  Frontend (Next.js) rules. Claude Code must follow these when working in frontend/.
  Loaded by frontend/CLAUDE.md. Enforced by frontend/scripts/check-conventions.mjs, ESLint and CI.
-->

# Frontend conventions (Next.js)

These conventions follow the official **Next.js 16 App Router** docs (`frontend/node_modules/next/dist/docs/01-app/01-getting-started/02-project-structure.md`) and the style used in the Next.js docs and examples. They are enforced automatically. Run everything locally from `frontend/`:

```bash
npm run check   # conventions + lint + typecheck
```

CI (`.github/workflows/ci.yml`, job **Frontend**) runs the same checks plus `next build` on every push and pull request. All paths below are relative to `frontend/`.

| Check           | Command                     | Enforced by                     |
| --------------- | --------------------------- | ------------------------------- |
| File/code rules | `npm run check:conventions` | `scripts/check-conventions.mjs` |
| Lint            | `npm run lint`              | `eslint.config.mjs`             |
| Types           | `npm run typecheck`         | `next typegen && tsc --noEmit`  |

## Folder structure

This app keeps `app/` for routing and puts shared code in top-level folders (the docs' "store project files outside of `app`" strategy):

```
app/          Routes: page, layout, loading, error, route, metadata files, ...
  blog/
    _components/   Route-specific components (private folder, not routable)
    _lib/          Route-specific helpers
components/   Shared React components
hooks/        Shared custom hooks
lib/          Helpers, constants, data, animation presets
public/       Static assets (always at the app root, frontend/public/)
scripts/      Node tooling scripts
```

An optional `frontend/src/` folder is supported (`src/app`, `src/components`, …). Don't keep both `app/` and `src/app/`: Next.js ignores `src/app` when `app/` exists.

## File & folder naming

**Use kebab-case for every file and folder.** This matches the Next.js special files (`not-found.tsx`, `global-error.tsx`) and the Next.js docs, which name component files like `nav-links.tsx` and `signup-form.tsx`. Inside the file, the component name stays PascalCase.

| Location          | Rule                                     | Example                                      |
| ----------------- | ---------------------------------------- | -------------------------------------------- |
| All files/folders | kebab-case                               | `components/project-card.tsx` → `export function ProjectCard()` |
| `hooks/`          | `use-` prefix, kebab-case                | `use-scroll-progress.ts` → `export function useScrollProgress()` |
| `public/`         | kebab-case, lowercase (`@2x` allowed)    | `hero-banner.webp`, `logo@2x.png`            |
| `app/` folders    | kebab-case or a Next.js folder convention | see below                                   |

Root config files (`next.config.ts`, `proxy.ts`, `instrumentation.ts`, …) are exempt.

### `app/` folder conventions

| Folder          | Meaning                                  |
| --------------- | ---------------------------------------- |
| `about`         | URL segment `/about` (kebab-case)        |
| `(marketing)`   | Route group, left out of the URL         |
| `[slug]`, `[postId]` | Dynamic segment (camelCase params are fine) |
| `[...slug]`, `[[...slug]]` | Catch-all / optional catch-all |
| `@modal`        | Parallel route slot                      |
| `(.)photo`, `(..)photo`, `(...)photo` | Intercepting routes |
| `_components`, `_lib` | Private folder, not routable       |

### `app/` file conventions

Code files directly inside route folders must be **Next.js special files**:

- Routing: `page`, `layout`, `template`, `loading`, `error`, `global-error`, `not-found`, `global-not-found`, `forbidden`, `unauthorized`, `default`, `route`
- Metadata: `favicon`, `icon`, `apple-icon`, `opengraph-image`, `twitter-image` (number suffixes such as `icon1` are allowed), `sitemap`, `robots`, `manifest`
- Stylesheets: `globals.css` and CSS modules such as `blog.module.css`

Any other colocated code goes in a private folder (`_components/`, `_lib/`) or in the top-level `components/` / `lib/`. The docs recommend this to separate UI from routing logic and to avoid clashing with future Next.js file names.

## Code rules

- **Module-level directives come first.** `"use client"`, `"use server"`, `"use cache"` (and `"use cache: private"` / `"use cache: remote"`) must be the first statement in the file, above the imports, or they are ignored. Function-level directives (`"use server"` / `"use cache"` inside a function body) are fine.
- **Interactive components declare `"use client"`.** Any `.tsx` in `app/` or `components/` that uses React client hooks (`useState`, `useEffect`, `useRef`, …), `next/navigation` hooks (`useRouter`, `usePathname`, …), `useGSAP` / `gsap`, `motion/react`, event handlers (`onClick={…}`), or browser globals (`window`, `document`, …) must start with `"use client"`. Put the directive on the interactive leaf components, not on whole pages or layouts.
- **Error boundaries are Client Components.** `error.tsx` and `global-error.tsx` must start with `"use client"`.
- **`server-only` modules are never `"use client"`.**
- **No `../../` imports.** Use the `@/` alias (`import { HeroSection } from "@/components/hero-section"`).
- **Named exports for shared components.** `export default` is for Next.js special files (`page.tsx`, `layout.tsx`, …), which require it.
- **Hook files export the matching hook.** `hooks/use-scroll-progress.ts` → `export function useScrollProgress()`.
- **Use `proxy.ts`, not `middleware.ts`.** `middleware` is deprecated in Next.js 16.

## Lint rules (on top of `eslint-config-next/core-web-vitals` + `eslint-config-next/typescript`)

The base is the configuration Next.js recommends. This project adds:

- No `console.log` (`console.warn` / `console.error` are allowed; `scripts/` is exempt).
- `===` instead of `==` (except `== null`).
- `const` over `let` when a variable is never reassigned; no `var`.
- Type-only imports use `import { type Foo }`.
- Unused variables are errors (prefix with `_` to ignore one on purpose).
- Self-closing JSX for empty elements, no `prop={true}`, no needless `{"string"}`.
- CI runs lint with `--max-warnings=0`, so warnings fail the build too.

## Commit messages & branches

Commit message, branch naming and branch workflow rules live in [`github.md`](github.md).

CI enforces commit messages with `commitlint.config.mjs`: every commit in a push or PR is checked, and so is the PR title, because it becomes the commit message when you squash-merge.

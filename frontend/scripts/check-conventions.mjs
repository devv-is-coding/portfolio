#!/usr/bin/env node
/**
 * Project convention checker.
 *
 * Enforces the file/folder/code conventions documented in .ai/rules/frontend.md (repo root)
 * that ESLint can't express well. Rules follow the Next.js 16 App Router docs
 * (node_modules/next/dist/docs/01-app/01-getting-started/02-project-structure.md).
 *
 * Runs locally (`npm run check:conventions`) and in CI. Exits 1 on any violation.
 */
import { existsSync, readdirSync, readFileSync, statSync } from "node:fs";
import { join, relative, sep, extname, basename } from "node:path";

const ROOT = process.cwd();

const IGNORED_DIRS = new Set([
  "node_modules",
  ".git",
  ".next",
  ".claude",
  ".ai",
  ".github",
  ".vercel",
  ".turbo",
  "out",
  "build",
  "coverage",
]);

const CODE_EXTS = new Set([".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".mts", ".cts"]);
const STYLE_EXTS = new Set([".css", ".scss", ".sass"]);

// ---------------------------------------------------------------------------
// Naming helpers
// ---------------------------------------------------------------------------
const KEBAB = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;
const HOOK_FILE = /^use-[a-z0-9]+(?:-[a-z0-9]+)*$/;

/** Strip every extension: "nav-links.test.tsx" -> "nav-links", "types.d.ts" -> "types". */
const stem = (file) => file.split(".")[0];

/** "use-scroll-progress" -> "useScrollProgress" */
const kebabToCamel = (s) => s.replace(/-([a-z0-9])/g, (_, c) => c.toUpperCase());

// Next.js App Router special files (without extension).
// Routing: docs/01-app/01-getting-started/02-project-structure.md#routing-files
// Metadata: docs/01-app/03-api-reference/03-file-conventions/01-metadata/
const NEXT_ROUTE_FILES = new Set([
  "page",
  "layout",
  "template",
  "loading",
  "error",
  "global-error",
  "not-found",
  "global-not-found",
  "forbidden",
  "unauthorized",
  "default",
  "route",
]);
// Metadata files; icons/OG images may have a number suffix (icon1.png, opengraph-image2.tsx).
const NEXT_METADATA_FILE = /^(favicon|icon\d*|apple-icon\d*|opengraph-image\d*|twitter-image\d*|sitemap|robots|manifest)$/;

/**
 * Valid App Router folder: kebab-case, or one of the Next.js folder conventions:
 * (group), [param], [...slug], [[...slug]], @slot, _private, %5Fescaped,
 * and intercepting routes (.)x, (..)x, (..)(..)x, (...)x.
 */
function isValidRouteSegment(name) {
  const inner = name
    .replace(/^(\((?:\.{1,3})\))+/, "") // intercepting: (.) (..) (..)(..) (...)
    .replace(/^\((.+)\)$/, "$1") // (group)
    .replace(/^\[\[\.\.\.(.+)\]\]$/, "$1") // [[...slug]]
    .replace(/^\[\.\.\.(.+)\]$/, "$1") // [...slug]
    .replace(/^\[(.+)\]$/, "$1") // [param]
    .replace(/^@/, "") // @slot
    .replace(/^(_|%5F)/i, ""); // _private / %5Fescaped
  // Dynamic params may be camelCase (e.g. [postId]).
  const isDynamic = /^(\(\.{1,3}\))*\[/.test(name);
  return KEBAB.test(inner) || (isDynamic && /^[a-z][a-zA-Z0-9]*$/.test(inner));
}

// ---------------------------------------------------------------------------
// Collect files
// ---------------------------------------------------------------------------
function walk(dir, out = []) {
  for (const entry of readdirSync(dir)) {
    if (IGNORED_DIRS.has(entry)) continue;
    const full = join(dir, entry);
    if (statSync(full).isDirectory()) {
      out.push({ path: full, dir: true });
      walk(full, out);
    } else {
      out.push({ path: full, dir: false });
    }
  }
  return out;
}

const entries = walk(ROOT).map((e) => {
  const rel = relative(ROOT, e.path).split(sep).join("/");
  // Support the optional `src/` folder: rules apply to `src/app`, `src/components`, ...
  const logical = rel.startsWith("src/") ? rel.slice(4) : rel === "src" ? "" : rel;
  return { ...e, rel, logical };
});

// ---------------------------------------------------------------------------
// Rules
// ---------------------------------------------------------------------------
const violations = [];
const report = (file, rule, message) => violations.push({ file, rule, message });

const segments = (p) => p.split("/");
const inPrivateFolder = (logical) => segments(logical).slice(0, -1).some((s) => /^(_|%5F)/i.test(s));
const isComponentsPath = (logical) => /^components\/|\/_components\//.test(logical);
const isHooksPath = (logical) => /^hooks\/|\/_hooks\//.test(logical);

// `src/app` is ignored by Next.js when a root `app/` exists.
if (existsSync(join(ROOT, "app")) && existsSync(join(ROOT, "src", "app"))) {
  report("src/app", "src-folder", "Both app/ and src/app/ exist. Next.js ignores src/app when app/ is present; keep only one.");
}

for (const { rel, logical, dir } of entries) {
  if (!logical) continue;
  const name = basename(rel);
  const top = segments(logical)[0];
  const isRootFile = !logical.includes("/");
  const ext = extname(name);
  const fileStem = stem(name);

  // --- Deprecated conventions ---------------------------------------------
  if (!dir && isRootFile && fileStem === "middleware" && CODE_EXTS.has(ext)) {
    report(rel, "middleware-deprecated", `"middleware" was renamed to "proxy" in Next.js 16. Run: npx @next/codemod@canary middleware-to-proxy .`);
  }

  // Root-level files (next.config.ts, proxy.ts, instrumentation.ts, README.md, ...) are exempt.
  if (!dir && isRootFile) continue;

  // --- Folder naming -------------------------------------------------------
  if (dir) {
    if (top === "app") {
      if (logical !== "app" && !isValidRouteSegment(name)) {
        report(rel, "folder-naming", `App Router folder "${name}" must be kebab-case (or a Next.js convention: (group), [param], @slot, _private, (..)intercept).`);
      }
    } else if (!KEBAB.test(name)) {
      report(rel, "folder-naming", `Folder "${name}" must be kebab-case.`);
    }
    continue;
  }

  // --- File naming ---------------------------------------------------------
  if (top === "public") {
    // Assets are served as URLs: keep them lowercase & kebab-case (optional @2x suffix).
    if (!KEBAB.test(fileStem.replace(/@\dx$/, ""))) {
      report(rel, "asset-naming", `Asset "${name}" must be kebab-case and lowercase (e.g. hero-banner.webp).`);
    }
    continue;
  }

  if (!CODE_EXTS.has(ext) && !STYLE_EXTS.has(ext)) continue;

  if (top === "app" && !inPrivateFolder(logical)) {
    const isSpecial = NEXT_ROUTE_FILES.has(fileStem) || NEXT_METADATA_FILE.test(fileStem);
    if (CODE_EXTS.has(ext) && !isSpecial) {
      report(
        rel,
        "app-colocation",
        `"${name}" is not a Next.js special file. Put it in a private folder (e.g. _components/, _lib/) or in the top-level components/ or lib/.`,
      );
    }
  }

  if (isHooksPath(logical) && CODE_EXTS.has(ext)) {
    if (fileStem !== "index" && !HOOK_FILE.test(fileStem)) {
      report(rel, "hook-naming", `Hook file "${name}" must be kebab-case and start with "use-" (e.g. use-scroll-progress.ts).`);
    }
  } else if (!KEBAB.test(fileStem)) {
    report(rel, "file-naming", `File "${name}" must be kebab-case (e.g. nav-links.tsx, format-date.ts). Component names stay PascalCase inside the file.`);
  }

  if (!CODE_EXTS.has(ext)) continue;
  checkContent(rel, logical, ext, readFileSync(join(ROOT, rel), "utf8"));
}

function checkContent(rel, logical, ext, source) {
  // Strip comments so commented-out code doesn't trigger rules.
  const code = source.replace(/\/\*[\s\S]*?\*\//g, "").replace(/(^|[^:"'`\\])\/\/.*$/gm, "$1");
  const lines = code.split(/\r?\n/);
  const top = segments(logical)[0];
  const fileStem = stem(basename(rel));

  // 1. Module-level directives must be the very first statement.
  //    Function-level directives ("use server" / "use cache" inside a function body) are indented and ignored here.
  const DIRECTIVE = /^["']use (client|server|cache(?:: ?(?:private|remote))?)["'];?\s*$/;
  const firstStatement = lines.map((l) => l.trim()).find((l) => l.length > 0) ?? "";
  const firstIsDirective = DIRECTIVE.test(firstStatement);
  lines.forEach((line, i) => {
    if (DIRECTIVE.test(line) && line.trim() !== firstStatement) {
      // Allow a stack of directives at the top only if everything above is also a directive.
      const above = lines.slice(0, i).map((l) => l.trim()).filter(Boolean);
      if (!above.every((l) => DIRECTIVE.test(l))) {
        report(`${rel}:${i + 1}`, "directive-position", `${line.trim()} must be the first statement in the file (above imports), otherwise it is ignored.`);
      }
    }
  });
  const isClient = firstIsDirective && /use client/.test(firstStatement);

  // 2. Error boundaries must be Client Components.
  if (top === "app" && (fileStem === "error" || fileStem === "global-error") && !isClient) {
    report(rel, "error-boundary-client", `${fileStem}.tsx must start with "use client" (error boundaries are Client Components).`);
  }

  // 3. Interactive/client-only code in .tsx/.jsx needs "use client" (recommended: mark the files
  //    that define interactive components, not whole trees).
  if ((top === "app" || isComponentsPath(logical)) && (ext === ".tsx" || ext === ".jsx") && !isClient) {
    const clientOnly = [
      [/\buse(State|Effect|LayoutEffect|InsertionEffect|Ref|Reducer|Context|Transition|Optimistic|ActionState|ImperativeHandle|SyncExternalStore|EffectEvent)\s*[<(]/, "React client hooks"],
      [/\buse(Router|Pathname|SearchParams|Params|SelectedLayoutSegments?)\s*\(/, "next/navigation client hooks"],
      [/\buseGSAP\s*\(/, "useGSAP"],
      [/from\s+["'](gsap|gsap\/[^"']+|@gsap\/react)["']/, "GSAP"],
      [/from\s+["']motion\/react(-client)?["']/, "motion/react"],
      [/\son[A-Z][a-zA-Z]*=\{/, "event handlers"],
      [/\b(window|document|localStorage|sessionStorage|navigator)\./, "browser globals"],
    ];
    for (const [re, what] of clientOnly) {
      if (re.test(code)) {
        report(rel, "missing-use-client", `Uses ${what} but is missing "use client" at the top of the file.`);
        break;
      }
    }
  }

  // 4. "server-only" modules can't be Client Components.
  if (isClient && /import\s+["']server-only["']/.test(code)) {
    report(rel, "server-only-in-client", `Imports "server-only" but is marked "use client".`);
  }

  // 5. No deep relative imports — use the "@/" alias instead.
  lines.forEach((line, i) => {
    if (/(?:from\s+|import\s*\(\s*|require\s*\(\s*)["'](?:\.\.\/){2,}/.test(line)) {
      report(`${rel}:${i + 1}`, "import-alias", `Avoid "../../" imports; use the "@/..." alias.`);
    }
  });

  // 6. Hook files export a hook matching the file name: use-scroll-progress.ts -> useScrollProgress.
  if (isHooksPath(logical) && fileStem !== "index" && HOOK_FILE.test(fileStem)) {
    const hookName = kebabToCamel(fileStem);
    const exportRe = new RegExp(`export\\s+(?:default\\s+)?(?:function\\s+${hookName}\\b|const\\s+${hookName}\\b)`);
    if (!exportRe.test(code)) {
      report(rel, "hook-export", `Hook file must export "${hookName}".`);
    }
  }

  // 7. Shared components use named exports; default exports are for Next.js special files.
  if (isComponentsPath(logical) && /\bexport\s+default\b/.test(code)) {
    report(rel, "named-exports", `Use a named export for components (e.g. "export function NavLinks()"), not "export default".`);
  }
}

// ---------------------------------------------------------------------------
// Output
// ---------------------------------------------------------------------------
const isCI = process.env.GITHUB_ACTIONS === "true";

if (violations.length === 0) {
  console.log(`✔ Conventions check passed (${entries.filter((e) => !e.dir).length} files scanned).`);
  process.exit(0);
}

console.error(`✖ Found ${violations.length} convention violation(s):\n`);
for (const { file, rule, message } of violations) {
  console.error(`  ${file}\n    [${rule}] ${message}\n`);
  if (isCI) {
    // GitHub Actions annotation — shows inline on the PR "Files changed" tab.
    const [path, line] = file.split(":");
    console.log(`::error file=${path}${line ? `,line=${line}` : ""},title=${rule}::${message}`);
  }
}
console.error("See .ai/rules/frontend.md (repo root) for the full list of rules.");
process.exit(1);

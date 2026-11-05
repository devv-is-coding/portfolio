import path from "node:path";
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Don't let `next dev` generate AGENTS.md; its instructions live in CLAUDE.md.
  agentRules: false,
  // Docker builds set NEXT_OUTPUT=standalone for a minimal self-contained server (see Dockerfile).
  // Vercel builds leave it unset and use Vercel's own output.
  output: process.env.NEXT_OUTPUT === "standalone" ? "standalone" : undefined,
  cacheComponents: true,
  partialPrefetching: true,
  // Monorepo: the repo root also has a package-lock.json (commitlint), so pin the
  // project root to frontend/ instead of letting Next.js infer the parent folder.
  outputFileTracingRoot: path.join(__dirname),
  turbopack: {
    root: path.join(__dirname),
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
};

export default nextConfig;

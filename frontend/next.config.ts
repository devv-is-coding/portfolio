import path from "node:path";
import type { NextConfig } from "next";

const isProduction = process.env.NODE_ENV === "production";

/*
 * Content Security Policy without nonces: a nonce makes every page render per request and
 * rules out Partial Prerendering and caching, so scripts and styles allow 'unsafe-inline'
 * (Next.js inlines its bootstrap). Everything else is locked down. Production only: `next dev`
 * needs eval and websockets. ImageKit serves the media (ik.imagekit.io) and takes the admin's
 * uploads (upload.imagekit.io); a custom ImageKit domain must be added here.
 */
const CONTENT_SECURITY_POLICY = [
  "default-src 'self'",
  "script-src 'self' 'unsafe-inline'",
  "style-src 'self' 'unsafe-inline'",
  "img-src 'self' blob: data: https://ik.imagekit.io",
  "font-src 'self'",
  "connect-src 'self' https://upload.imagekit.io",
  "object-src 'none'",
  "base-uri 'self'",
  "form-action 'self'",
  "frame-ancestors 'none'",
].join("; ");

const SECURITY_HEADERS = [
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
  { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=(), browsing-topics=()" },
  ...(isProduction
    ? [
        { key: "Content-Security-Policy", value: CONTENT_SECURITY_POLICY },
        // Ignored over plain HTTP; behind the HTTPS proxy it keeps browsers on HTTPS.
        { key: "Strict-Transport-Security", value: "max-age=63072000; includeSubDomains" },
      ]
    : []),
];

const nextConfig: NextConfig = {
  // Don't let `next dev` generate AGENTS.md; its instructions live in CLAUDE.md.
  agentRules: false,
  poweredByHeader: false,
  async headers() {
    return [{ source: "/:path*", headers: SECURITY_HEADERS }];
  },
  // Docker builds set NEXT_OUTPUT=standalone for a minimal self-contained server (see Dockerfile).
  // Vercel builds leave it unset and use Vercel's own output.
  output: process.env.NEXT_OUTPUT === "standalone" ? "standalone" : undefined,
  images: {
    // AVIF first: about half the bytes of WebP for the hero portrait, which is the LCP on phones.
    formats: ["image/avif", "image/webp"],
  },
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

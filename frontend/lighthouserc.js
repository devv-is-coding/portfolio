/**
 * Lighthouse CI budgets (`npm run check:budgets`): three mobile runs per page, median against
 * the targets in TODO.md (performance >= 0.95, LCP < 2.5 s, CLS < 0.1, TBT < 200 ms as the lab
 * stand-in for INP, at most 160 KB of JavaScript).
 *
 * Locally it serves the last `npm run build` on port 3210 (the dev server owns 3000) against
 * the API in .env.local. CI sets LHCI_BASE_URL to the running production stack instead.
 */
const baseUrl = process.env.LHCI_BASE_URL;
const origin = baseUrl ?? "http://localhost:3210";
const pages = ["/", "/about", "/projects", "/blog", "/contact"];
const median = (value) => ["error", { ...value, aggregationMethod: "median" }];

module.exports = {
  ci: {
    collect: {
      ...(baseUrl
        ? {}
        : { startServerCommand: "npm run start -- --port 3210", startServerReadyPattern: "Ready" }),
      url: pages.map((page) => new URL(page, origin).href),
      numberOfRuns: 3,
      settings: { chromeFlags: "--headless=new --no-sandbox" },
    },
    assert: {
      assertions: {
        "categories:performance": median({ minScore: 0.95 }),
        "largest-contentful-paint": median({ maxNumericValue: 2500 }),
        "cumulative-layout-shift": median({ maxNumericValue: 0.1 }),
        "total-blocking-time": median({ maxNumericValue: 200 }),
        "resource-summary:script:size": median({ maxNumericValue: 160000 }),
      },
    },
    upload: { target: "filesystem", outputDir: ".lighthouseci" },
  },
};

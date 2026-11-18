import { fileURLToPath } from "node:url";
import { defineConfig } from "vitest/config";

// Run through `npm test` (scripts/run-vitest.mjs), which fixes the drive-letter case on Windows.
export default defineConfig({
  resolve: {
    alias: {
      "@": fileURLToPath(new URL(".", import.meta.url)),
      // The real package throws outside React Server Components; unit tests run plain Node.
      "server-only": fileURLToPath(new URL("node_modules/server-only/empty.js", import.meta.url)),
    },
  },
  test: {
    include: ["**/*.test.ts", "**/*.test.tsx"],
    exclude: ["node_modules/**", ".next/**"],
    environment: "node",
  },
});

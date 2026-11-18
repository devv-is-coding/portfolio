#!/usr/bin/env node
/**
 * Runs Vitest (`npm test`) from the canonical project path.
 *
 * On Windows a working directory with a lowercase drive letter (`c:\...`, common in VS Code
 * terminals) makes Vitest load itself twice, and every test file fails with "Vitest failed to
 * find the runner". Starting it from `C:\...` avoids that; elsewhere this is a plain pass-through.
 */
import { spawnSync } from "node:child_process";
import { join } from "node:path";

const cwd = process.cwd().replace(/^[a-z]:/, (drive) => drive.toUpperCase());
const cli = join(cwd, "node_modules", "vitest", "vitest.mjs");

const { status } = spawnSync(process.execPath, [cli, ...process.argv.slice(2)], {
  cwd,
  stdio: "inherit",
});
process.exit(status ?? 1);

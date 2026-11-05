/**
 * Conventional Commits — https://www.conventionalcommits.org
 * Format: <type>(<optional scope>): <subject>
 * e.g.   feat(hero): add GSAP scroll reveal
 */
const config = {
  extends: ["@commitlint/config-conventional"],
  rules: {
    "type-enum": [
      2,
      "always",
      ["feat", "fix", "style", "refactor", "perf", "docs", "test", "build", "ci", "chore", "revert"],
    ],
    "subject-case": [2, "never", ["sentence-case", "start-case", "pascal-case", "upper-case"]],
    "header-max-length": [2, "always", 72],
  },
};

export default config;

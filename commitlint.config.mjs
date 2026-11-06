/**
 * Commit message rules from .ai/rules/github.md (Conventional Commits).
 * Format: <type>(<scope>): <short description>
 * e.g.   feat(auth): add Google authentication
 *        feat(api)!: change response format
 */

// "never vague (`update`, `changes`, `fixed stuff`, `misc`)"
const VAGUE_SUBJECTS = new Set([
  "update",
  "updates",
  "change",
  "changes",
  "fix",
  "fixes",
  "fixed stuff",
  "fix stuff",
  "stuff",
  "misc",
  "wip",
  "minor changes",
  "minor fixes",
  "tweaks",
]);

// "imperative wording (`add`, `fix`, `update`, `remove`)": reject past tense / -ing starts.
const NON_IMPERATIVE_STARTS = new Set([
  "added", "adding", "fixed", "fixing", "updated", "updating", "removed", "removing",
  "changed", "changing", "created", "creating", "deleted", "deleting", "implemented",
  "implementing", "refactored", "refactoring", "moved", "moving", "renamed", "renaming",
  "improved", "improving", "replaced", "replacing", "upgraded", "upgrading", "bumped",
  "bumping", "cleaned", "cleaning", "adjusted", "adjusting", "resolved", "resolving",
]);

const config = {
  extends: ["@commitlint/config-conventional"],
  plugins: [
    {
      rules: {
        "subject-not-vague": ({ subject }) => {
          if (!subject) return [true];
          const normalized = subject.trim().toLowerCase().replace(/[.!]+$/, "");
          return [
            !VAGUE_SUBJECTS.has(normalized),
            `description "${subject}" is too vague; say what changed (e.g. "fix: resolve payment status issue")`,
          ];
        },
        "subject-imperative": ({ subject }) => {
          if (!subject) return [true];
          const first = subject.trim().split(/\s+/)[0].toLowerCase();
          return [
            !NON_IMPERATIVE_STARTS.has(first),
            `description must use imperative wording ("add", "fix", "update", "remove"), not "${first}"`,
          ];
        },
      },
    },
  ],
  rules: {
    "type-enum": [
      2,
      "always",
      ["feat", "fix", "refactor", "style", "docs", "test", "perf", "build", "ci", "chore", "revert"],
    ],
    // Lowercase type and scope come from config-conventional; keep descriptions out of
    // Sentence/Start/Pascal/UPPER case while allowing proper nouns ("add Google authentication").
    "subject-case": [2, "never", ["sentence-case", "start-case", "pascal-case", "upper-case"]],
    // "concise, preferably under 72 characters"
    "header-max-length": [2, "always", 72],
    "subject-not-vague": [2, "always"],
    "subject-imperative": [2, "always"],
  },
};

export default config;

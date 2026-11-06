/**
 * Rules for PR titles: a PR title is a single line, so it follows the commit-title rules
 * from commitlint.config.mjs without the body rules.
 *   echo "feat(backend): add mariadb and alembic" | npx commitlint --config commitlint.title.config.mjs
 */
import base from "./commitlint.config.mjs";

const config = {
  ...base,
  rules: {
    ...base.rules,
    "body-detailed": [0],
    "body-leading-blank": [0],
    "body-max-line-length": [0],
  },
};

export default config;

---
paths:
  - '.github/**'
---

# Github

## Commit messages follow Conventional Commits
Applies to every commit, not only to files under this path (commits touch no single file).
- Format `<type>(<scope>): <short description>`, e.g. `feat(auth): add Google authentication`, `fix(booking): resolve payment status issue`.
- Types: `feat` (new feature), `fix` (bug fix), `refactor` (restructuring, no behavior change), `style` (formatting, styling or UI-only), `docs`, `test`, `perf`, `build` (build system, dependencies, Docker, build configuration), `ci`, `chore` (general maintenance), `revert`.
- Lowercase type, scope and description; imperative wording (`add`, `fix`, `update`, `remove`); concise, preferably under 72 characters; never vague (`update`, `changes`, `fixed stuff`, `misc`).
- Inspect the actual changes first and choose the type from them. Use a scope when it makes the change clearer, never forced. Mark breaking changes with `!`: `feat(api)!: change response format`.
- Commit only when the user explicitly asks or the task requires it, and follow the branch rules below.

## Branch names and branch workflow
Applies to every branch, push and pull request.
- Name branches `<type>/<short-description>`, or `<type>/<issue-number>-<short-description>` when the work tracks a GitHub issue: lowercase, words separated by hyphens, concise and specific (`feat/42-tenant-directory`), no spaces, vague names or unnecessary dates.
- Branch types are **the same as commit types**: `feat/`, `fix/`, `refactor/`, `style/`, `docs/`, `test/`, `perf/`, `build/`, `ci/`, `chore/`, `revert/`. Urgent production fixes are `fix/` too. Branch `feat/tenant-management` → commit `feat: implement tenant management`. CI's **Branch name** check rejects pull requests from branches that don't match.
- `main` is stable, production-ready code and the only permanent branch. Never add `develop` or another permanent branch.
- **Never commit to `main`.** Every commit goes on a sub-branch created from an up-to-date `main`, and reaches `main` only through a pull request (squash merge, PR title in Conventional Commits format). Before branching, inspect the current branch and the working tree. If you're already on a sub-branch for the same task, keep committing there instead of creating a new branch for every small step.
- Never switch branches when that could overwrite, discard or interfere with uncommitted user changes; never discard user changes or run destructive Git operations without explicit authorization; never create, rename, delete or switch branches without considering the user's workflow. Do not rename or delete existing branches just to enforce these names.
- Cleanup, without asking, so local branches don't pile up. Before creating a new sub-branch:
  1. Update `main`: `git switch main && git pull --ff-only && git fetch --prune`.
  2. Find merged sub-branches. A sub-branch counts as merged when `git branch --merged main` lists it, **or** when `git branch -vv` shows its upstream as `[gone]`. A `[gone]` upstream means its PR was squash-merged and GitHub deleted the remote branch; Git can't detect squash merges with `--merged`.
  3. Keep only the most recently merged sub-branch as a rollback point, and delete every older merged one. So as soon as a second merged sub-branch exists, delete the older one. Use `git branch -d` for branches `--merged` lists, and `git branch -D` only for `[gone]` branches.
  4. Never delete the checked-out branch, a branch whose remote still exists and isn't merged, or a branch that has no upstream and isn't listed by `--merged`.

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
- **The title carries the information** the short branch name leaves out: name what was added or changed, e.g. `feat(payments): add payments, refunds and stripe webhooks`, not `feat: add payments`.
- **Every commit has a detailed body**, separated from the title by a blank line and wrapped at about 72 characters. Write one paragraph per task or part: what was built, how it behaves (limits, edge cases, what it refuses), and the key decisions and why. Name the real classes, functions, settings and env vars. Start a paragraph with the task or issue reference when there is one (`TA-18:`, `#42:`). Trailers such as `Co-Authored-By:` don't count as the body. Example:

  ```
  feat(payments): add payments, refunds and stripe webhooks

  TA-18: PaymentService records cash and bank transfers by staff (never
  more than the balance) and Stripe payments from the webhook, idempotent
  on the Stripe invoice. The booking's paid and refunded amounts are summed
  from the ledgers under a row lock; its payment status is derived by
  BookingPaymentStatus::fromAmounts().

  TA-19: laravel/cashier for the Stripe client and signature check; the
  platform collects. Cashier's routes are off: a central-only webhook
  refuses every event until STRIPE_WEBHOOK_SECRET is set. StripeGateway
  makes balance-only hosted invoices and refunds, never inside a DB
  transaction, with idempotency keys.

  TA-20: RefundService requests, approves (in full or less), rejects and
  processes refunds, several per booking, never more than was paid. A
  full refund cancels the booking and frees its units.
  ```
- Never commit unless the user explicitly says so, local commits included; no task or workflow is a reason to commit on your own. Then follow the branch rules below.

## Branch names and branch workflow
Applies to every branch, push and pull request.
- Name branches `<type>/<short-description>`, or `<type>/<issue-number>-<short-description>` when the work tracks a GitHub issue: lowercase, words separated by hyphens, concise and specific (`feature/42-tenant-directory`), no spaces, vague names or unnecessary dates.
- **Keep branch names short: 1–4 words naming the general area** (`feature/availability-and-booking`, `feature/backend-database`), never a list of everything in it. The details belong in the commit titles and bodies. CI rejects longer names.
- Types: `feature/`, `fix/`, `hotfix/` (urgent production fixes), `refactor/`, `docs/`, `test/`, `chore/` (maintenance, dependencies, tooling), `style/`, `perf/`. `main` is stable, production-ready code; `develop` exists only if the project uses that workflow. Branch and commit prefixes differ: branch `feature/tenant-management`, commit `feat: implement tenant management`.
- Create a branch when the task, its risk or the project's workflow warrants it, not for every small action. First inspect the current branch, the working tree and the repository's instructions, and follow the documented branching strategy; never add `develop` or another permanent branch unnecessarily.
- Prefer feature branches and pull requests for changes that need isolation or review. Never commit directly to `main` unless the user or the established workflow explicitly permits it.
- Never switch branches when that could overwrite, discard or interfere with uncommitted user changes; never discard user changes or run destructive Git operations without explicit authorization; never create, rename, delete or switch branches without considering the user's workflow. Do not rename or delete existing branches just to enforce these names.
- Cleanup, without asking: when creating a new sub-branch, check `git branch --merged main` and delete the merged branches except the single most recently merged one, kept as a rollback point. Never delete a branch not merged into `main`, or the one checked out.

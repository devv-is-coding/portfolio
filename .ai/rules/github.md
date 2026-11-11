---
paths:
  - '.github/**'
---

# Github

## Commits
- Never commit unless the user explicitly says so, local commits included.
- Conventional Commits: `<type>(<scope>): <description>`, lowercase, imperative, under 72 characters, never vague. Types: `feat`, `fix`, `refactor`, `style`, `docs`, `test`, `perf`, `build` (dependencies, Docker), `ci`, `chore`, `revert`. Breaking: `feat(api)!: ...`. Choose the type from the actual changes.
- The title names what changed (`feat(payments): add payments, refunds and stripe webhooks`, not `feat: add payments`).
- Every commit has a body: one paragraph per task (what was built, how it behaves, key decisions), real names of classes and settings, wrapped at ~72 characters, task reference first when there is one. Trailers don't count. Example:

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
  ```

## Branches
- `<type>/<1-4-words>` (or `<type>/<issue>-<words>`), lowercase, hyphens; CI rejects longer names. Types: `feature/`, `fix/`, `hotfix/`, `refactor/`, `docs/`, `test/`, `chore/`, `style/`, `perf/`. Branch `feature/...`, commit `feat: ...`.
- Never commit to `main` directly; no extra permanent branches.
- Never switch branches over uncommitted changes, discard user changes, or run destructive Git operations without permission. Don't rename or delete existing branches just to enforce names.
- Cleanup when creating a branch: delete branches in `git branch --merged main` except the most recently merged one (rollback point). Never delete an unmerged or checked-out branch.

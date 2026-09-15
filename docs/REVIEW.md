---
id: review
type: review
---

# Human Attention Log

Items below need human review. Agents append when making a decision not covered by
existing docs, or when they hit a doc-first conflict. A human resolves each item
APPROVED or OVERRIDDEN; the agent then propagates the decision into the source doc.

## Open Items

- **2026-09-15 — Stale backend design docs.** `backend/docs/README.md` and
  `backend/docs/QUICK_START.md` are dated 2026-01-20 and describe the v2.0 backend as
  "Design Phase Complete / Ready For Implementation". The code shipped long since, and both
  files link to a `../DESIGN.md` that does not exist. Left untouched by `/tai-docs-init` per
  explicit user choice. A human should decide whether to reconcile, archive, or delete them.

- **2026-09-15 — `docs/changelog.md` and `docs/contributing.md` deliberately absent.** Root
  `CHANGELOG.md` and `CONTRIBUTING.md` remain canonical, per explicit user choice, to avoid
  two copies drifting apart. Skills expecting the `docs/` paths should read the root files.

## Resolved Items


- **2026-09-15 — Alembic migration history is broken; the live DB is ahead of `main`.**
  RESOLVED in commit 88c0cf9 on branch `fix/alembic-history`. Two causes, not one. The
  revision files for `add_session_summary_20260308` and the merge `291e73a4c1bd` existed
  only in commit `6b302e5` on the unmerged branch `feat/session-memory-20260308`; both
  were restored verbatim. Separately, `alembic history` hung on a 13-revision cycle
  dating from January — `def789ghi012` (2026-01-21 03:19) declared `down_revision`
  `"abc123def456"`, a hand-typed placeholder that a real revision created on 2026-01-23
  happened to reuse, closing the loop. Repointed at `0cd45723ec3c`, its true predecessor.
  Verified: single head, `history` completes, `upgrade head` is a clean no-op. The
  hand-ALTERed `sessions.task_id` noted in the original item is unchanged — it remains a
  plain `TEXT REFERENCES tasks(id)` without the constraints its migration declares, which
  is cosmetic on SQLite but should be revisited before any PostgreSQL deployment.

---
id: review
type: review
---

# Human Attention Log

Items below need human review. Agents append when making a decision not covered by
existing docs, or when they hit a doc-first conflict. A human resolves each item
APPROVED or OVERRIDDEN; the agent then propagates the decision into the source doc.

## Open Items

- **2026-09-15 — Alembic migration history is broken; the live DB is ahead of `main`.**
  `~/.kumiai/kumiai.db` reports revision `add_session_summary_20260308`, but that revision's
  `.py` is not on `main` — only a stale `.pyc` under `alembic/versions/__pycache__/`. The same
  applies to the merge revision `20260308_1553_..._merge_cli_backend_and_task_layer`. Both
  exist only in commit `6b302e5` on the unmerged branch `feat/session-memory-20260308`.
  `alembic heads` therefore reports two heads (`20260305_0000`, `add_task_layer_20260308`),
  `alembic upgrade head` fails with "Can't locate revision", and no new migration can pick an
  unambiguous `down_revision`. This also explains why `sessions.task_id` is in the live schema
  as a hand-ALTERed `TEXT REFERENCES tasks(id)` with none of the constraints its migration
  declares. **Blocks any schema change repo-wide.** Owner decided 2026-09-15 to fix it on a
  separate branch, merged before `feat/session-parent-notify` proceeds.

- **2026-09-15 — Stale backend design docs.** `backend/docs/README.md` and
  `backend/docs/QUICK_START.md` are dated 2026-01-20 and describe the v2.0 backend as
  "Design Phase Complete / Ready For Implementation". The code shipped long since, and both
  files link to a `../DESIGN.md` that does not exist. Left untouched by `/tai-docs-init` per
  explicit user choice. A human should decide whether to reconcile, archive, or delete them.

- **2026-09-15 — `docs/changelog.md` and `docs/contributing.md` deliberately absent.** Root
  `CHANGELOG.md` and `CONTRIBUTING.md` remain canonical, per explicit user choice, to avoid
  two copies drifting apart. Skills expecting the `docs/` paths should read the root files.

## Resolved Items

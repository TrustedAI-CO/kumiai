---
id: plan-backlog
type: plan
---

# Backlog

## Active
Scheduled deferred work — will do, just not this PR.
- [ ] `BLOCKED` session status + stream-based blocked inference (a session waiting on a
      permission prompt or a clarifying question cannot self-report; it must be observed) —
      deferred 2026-09-15, split out of the parent-notify work
- [ ] Fan-out join/barrier primitive so a coordinator wakes once when a spawned set
      resolves, instead of once per child — deferred 2026-09-15, same split

## Backlog (someday / declined)
Unscheduled — someday / maybe / declined ideas + tech debt.
- **Warn before deleting a project with running agents.** A confirmation showing how many
  agents will be stopped. *Why:* `SPEC-work-project-delete-cascade` R3 stops live agents
  silently, and the count is already computed at delete time — deleting mid-run gives no
  signal that work-in-progress is being killed. *Pros:* makes an irreversible side effect
  visible, nearly free since the count is in hand. *Cons:* adds a round trip to a soft
  action, and it is frontend work on top of a backend PR. *Context:* raised as the Open
  Question on `SPEC-work-project-delete-cascade`, 2026-09-15; excluded so that spec's rules
  stay API-level. Start at the delete confirmations in `frontend/src/pages/Projects.tsx:298`
  and `frontend/src/components/.../WorkplaceKanban.tsx:410`. *Depends on:* WORK-01 shipping.
- **The phantom `cancel_instance` MCP tool.** Either implement it or stop advertising it.
  *Why:* `backend/app/domain/config/system_prompts.py:79` tells every PM agent it has a
  `cancel_instance` tool for stopping a running specialist. No implementation exists — grep
  finds only the prompt line. PMs are instructed to call something that fails, and a
  coordinator has no way to stop a runaway child. *Pros:* `SessionExecutor.interrupt()`
  already does the work, so implementing is small; either outcome stops lying to the agent.
  *Cons:* implementing means a new MCP surface with its own spec and gate; removing the line
  is trivial but leaves PMs unable to stop children. *Context:* found 2026-09-15 while
  hunting for a teardown path to reuse for WORK-01. An **uncommitted, unmerged** edit on
  branch `feat/session-parent-notify` already deletes this prompt line and may resolve half
  of it. Start at `backend/app/infrastructure/mcp/servers/pm_management.py`.
  *Depends on:* nothing.
- **Permanent purge (real delete) for projects.** Destroy a project, its children, its
  messages, and optionally its files. *Why:* after WORK-01/02 every deleted project is kept
  forever — rows, conversation history and disk. The live DB was already 17/23 soft-deleted
  on 2026-09-15, and nothing reclaims that. *Pros:* bounded storage, genuine removal for
  anything sensitive, and the `ON DELETE CASCADE` FKs at `models.py:139`/`models.py:280`
  would finally do their job on a hard delete. *Cons:* truly irreversible, so it needs a
  confirmation design; it interacts with restore (purge must refuse or invalidate one); and
  it reopens the "leave files on disk" decision that WORK-01 R5 settled. *Context:* noted
  2026-09-15 while specifying soft-delete semantics; listed as an Open Question on
  `SPEC-work-project-restore`. Not urgent at 23 projects, matters at 1000.
  *Depends on:* WORK-01 and WORK-02 — purge semantics follow from what restore promises.
- **Break the executor circular dependency.** `SessionStatusManager` and the MCP tools reach
  the executor through a lazy `from app.api.dependencies import get_session_executor` inside
  the function body — a workaround for a circular import between the API and infrastructure
  layers. *Why:* it hides a real dependency, makes the executor untestable without the API
  package, and every new caller copies the workaround (COORD-03's notifier now does too).
  *Pros:* honest dependency graph, injectable executor, simpler tests. *Cons:* touches
  wiring used by every session path; a structural refactor with a wide blast radius.
  *Context:* deliberately excluded from the parent-notify change on 2026-09-15 — mixing a
  structural refactor into a behavioral change would have made both harder to review. Start
  at `app/api/dependencies.py` and the constructor of `SessionExecutor`.
  *Depends on:* nothing; best done on a quiet branch.
- **Structured payload on runtime notifications.** COORD-02 delivers human-readable prose. A
  future join/barrier primitive would have to parse it. *Why:* machine consumers should not
  regex agent-facing text. *Context:* noted 2026-09-15 as an open question on
  `SPEC-coord-parent-notification`; blocked on the barrier work below actually being started.
  *Depends on:* the fan-out join/barrier item in `## Active`.
- `backend/docs/README.md` + `backend/docs/QUICK_START.md` are dated 2026-01-20, labelled
  "Design Phase Complete / Ready For Implementation", and link to a `../DESIGN.md` that no
  longer exists — noted 2026-09-15, needs human reconciliation (see `docs/REVIEW.md`)
- Let agents shape the kanban view (grouping, pinning, ad-hoc swimlanes) rather than only
  moving cards through fixed columns — noted 2026-09-15, from herdr analysis
- Durability for in-flight runs: conversation history is persisted but an executing run
  lives in the uvicorn process — noted 2026-09-15, from herdr analysis

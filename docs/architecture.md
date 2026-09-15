---
id: architecture
type: architecture
---

# Architecture — Module list (shape)

The named capabilities the code is organized into — the stable home a feature lives in. A
feature points here with `module: <name>`.

Decomposition axis for this project: **bounded domains**. Cross-cutting infrastructure
(`persistence`) is the small tail, not a peer capability.

## Modules

| module               | role                                                                                      | depends-on                                        |
|----------------------|-------------------------------------------------------------------------------------------|---------------------------------------------------|
| agent-runtime        | Runs an agent turn against a CLI backend and parses its event stream into domain events     | persistence                                       |
| session-coordination | Owns session lifecycle, the status state machine, spawning, and inter-session message delivery | agent-runtime, persistence                        |
| project-workspace    | Project → Task → Session hierarchy and the kanban stages work moves through                 | persistence                                       |
| agent-catalog        | Agent definitions and skills stored on the filesystem, plus their authoring assistants      | persistence                                       |
| mcp-tools            | MCP servers that expose product actions (spawn, contact, task CRUD) to running agents       | session-coordination, project-workspace, agent-catalog |
| http-api             | FastAPI routes and the SSE transport that streams agent activity to clients                 | session-coordination, project-workspace, agent-catalog |
| web-ui               | React client — kanban board, session chat, agent/skill management                           | http-api                                          |
| persistence          | SQLAlchemy models, repositories, and Alembic migrations over SQLite                         | —                                                 |

## Module details

### agent-runtime
`backend/app/infrastructure/claude/` and `backend/app/infrastructure/cli/`. Launches the
configured CLI backend (`claude`, `codex`, `gemini`, `opencode`), feeds it a prompt, and
parses the backend-specific stream into a common `ParsedEvent` shape. Owns execution
concerns the product should not see: retries on recoverable errors, hooks that inject
session context into tool calls, and the queue processor that serialises turns for a
session. Backend selection lives in `cli/detector.py` and `cli/config.py`.

### session-coordination
`backend/app/application/services/session_service.py`,
`backend/app/domain/entities/session.py`,
`backend/app/domain/value_objects/session_status.py`, and
`backend/app/infrastructure/claude/state/session_status_manager.py`. A session is one agent
instance working inside a project. This module decides what states a session may occupy and
what transitions are legal, spawns child sessions, and delivers messages between sessions by
waking the target and enqueuing to its executor. It is the module a coordinator agent depends
on to learn that delegated work finished.

### project-workspace
`backend/app/application/services/{project_service,task_service}.py` and the matching
entities. Holds the organisational structure — a project groups tasks, a task groups the
sessions working toward it — and the kanban stage each item sits in. Deliberately separate
from `session-coordination`: this module answers "how is the work organised", not "what is
the agent doing right now".

Deletion is soft throughout the hierarchy — a `deleted_at` stamp, never a row removal. That
makes the database-level `ON DELETE CASCADE` on `sessions.project_id` and `tasks.project_id`
inert (a soft delete is an `UPDATE`), so the cascade is the service's job, and it reaches
across the module boundary into `session-coordination` to stop live agents before hiding
their project:

```
delete_project(id)
  │
  ├─1─ stop live agents        ──► session-coordination: SessionExecutor.interrupt(sid)
  │     best-effort, failures logged, never aborts the delete   [not transactional]
  │
  ├─2─ one transaction, one shared timestamp T
  │     project.deleted_at        = T
  │     tasks WHERE project_id    = T   (only those still live)
  │     sessions WHERE project_id = T   (only those still live)
  │
  └─3─ files under ~/.kumiai/projects/  ── untouched, by design

restore_project(id)
      un-hide the project + exactly the children stamped T
      children deleted before T carry an earlier stamp and stay deleted
```

`T` is load-bearing: it is the only thing distinguishing "hidden because the parent was
deleted" from "already deleted earlier", which is what makes restore correct without an
extra column. Agent teardown is ordered before the commit because stopping an agent is
irreversible while hiding a project is not — a stopped agent after a failed commit is
visible and restartable; an agent still running against a deleted project spends real money
invisibly.

### agent-catalog
`backend/app/infrastructure/filesystem/{agent_repository,skill_repository}.py` and
`backend/app/application/services/{agent_service,skill_service}.py`. Agents and skills are
markdown-and-frontmatter artifacts on disk, not database rows, so they can be authored,
imported from GitHub, and version-controlled by hand. Includes the assistant tooling that
helps a user write a `SKILL.md` or an agent definition.

### mcp-tools
`backend/app/infrastructure/mcp/servers/`. The surface an agent sees. Every tool here is a
product action with a visible consequence — `spawn_instance` creates a real session,
`contact_instance` wakes a real peer — as opposed to the CLI's own built-in sub-agent
tooling, which is invisible to the product. Context (`source_instance_id`, `project_id`) is
injected by a runtime hook rather than trusted from the agent.

### http-api
`backend/app/api/routes/` plus `backend/app/infrastructure/sse/manager.py`. REST for CRUD
and an SSE channel per session so a client can watch an agent think in real time.

### web-ui
`frontend/src/`. React + TypeScript + Vite. Kanban board with drag-to-restage, task
drill-down, session chat, and agent/skill management screens.

### persistence
`backend/app/infrastructure/database/` and `backend/alembic/`. SQLAlchemy models and
repository implementations behind the domain's repository interfaces, over SQLite at
`~/.kumiai/kumiai.db`. Schema changes go through Alembic; nothing else writes DDL.

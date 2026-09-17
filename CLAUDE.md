# Project rules for AI coding agents

> **Keeping this alive:** Read by AI on every task, so wrong content here causes wrong code *everywhere* — treat it like config. Keep it short and at the conventions/architecture level; never mirror the codebase in prose. Update it in the *same PR* as any convention or structure change. If a rule no longer holds, delete it — a stale rule is worse than none.

## What this project is

KumiAI is a project-level multi-agent system built on Claude Code. A user assembles agents
from reusable skills, groups work as Project → Task → Session, and watches the agents
collaborate live on a kanban board. Backend is Python 3.11 + FastAPI over SQLite
(`backend/app`, clean-architecture layers `api / application / domain / infrastructure`);
frontend is React 18 + TypeScript + Vite (`frontend/src`, dev on port 1420). Agent execution
runs real CLI backends (`claude`, `codex`, `gemini`, `opencode`) and parses their event
streams. Module map: `docs/architecture.md`.

## Conventions

- Python: Black + Ruff (both pinned in `.pre-commit-config.yaml`, scoped to `backend/`).
  Type hints on public functions; `mypy` runs but is not gating.
- TypeScript: `tsc --noEmit` must pass (`npm run typecheck` in `frontend/`).
- Clean architecture is enforced by direction, not tooling: `domain` imports nothing from
  `infrastructure`; `application` orchestrates; `api` is transport only. Repository
  interfaces live in `domain/repositories`, implementations in `infrastructure/database`.
- Domain entities are dataclasses with behavior — state changes go through entity methods
  that raise `InvalidStateTransition`, never by assigning `.status` from outside.
- Immutability: prefer returning new objects over mutating inputs.
- Errors: raise typed exceptions from `app/core/exceptions.py`; never swallow silently. MCP
  tool handlers are the exception — they catch and return a `_error(...)` envelope, because
  an exception there would break the agent's turn.
- Schema changes go through Alembic (`backend/alembic/versions/`). Nothing else writes DDL.
- Branching: `main` is deployable. `feat/...`, `fix/...`.
- Commits: Conventional Commits.
- Gotcha: agent-facing MCP tools receive `source_instance_id` / `project_id` via the
  `inject_session_context_hook`, not from the agent's arguments. Never trust an agent to
  supply its own identity.
- Gotcha: sessions may be stored with `task_id = NULL` (pre-task-layer rows). Treat the task
  link as optional everywhere.

## Testing

- Run tests with: `cd backend && source .venv/bin/activate && pytest`
- Framework: pytest 8+ (`backend/pytest.ini`); tests in `backend/tests/`, split
  `unit/ integration/ e2e/ smoke/`. See `backend/tests/TESTING_GUIDE.md`.
- Coverage: `pytest --cov` (configured over `app`). Target 80%.
- Philosophy: unit-heavy for domain/state-machine logic, integration for routes and
  repositories.
- Each test tags the spec rule it covers: `# spec: SPEC-x R3`.

## Always

- Run `pytest` (backend) / `npm run typecheck` (frontend) before declaring a task done.
- Update `docs/` when behavior or architecture changes.

## Note capture reflex

- When the user declines or defers a suggestion, append one line to `docs/plan/backlog.md`
  before continuing — don't lose it, don't act on it.

## Never

- Don't commit secrets or edit `.env`.
- Don't change a public surface without updating its spec first.
- Don't start dev servers with `tmux send-keys` — a hook blocks it. Pass the command as an
  argument to `tmux new-session` instead.

## Doc-first rule (the core discipline)

Docs are ground truth; code is derived. **Change the spec before the code.**
- Before editing code for a feature, open its `docs/specs/<area>-<name>.md` and change it first.
- Tag implementing source files with `# feature: <functions id>` and tests with `# spec: SPEC-x Rn`.
- The spec's Behavior rows are the test contract. Make the code pass them; never rewrite the
  spec to match code you already wrote — that inverts the order.
- A human approves a spec (`python scripts/trace.py approve SPEC-x`); `trace.py audit` warns
  while code runs ahead of an unapproved spec (non-blocking).

## Layers & ownership

- `docs/intent.md` — product goals `Gn` (WHY). **HUMAN-owned.**
- `docs/architecture.md` — the module list (SHAPE). Engineer.
- `docs/functions.md` — the feature registry (WHAT). Owner sets `importance`/`scope`.
- `docs/specs/` — behavioral contracts (`Rn`). Agents draft; a human approves `status`.
- code + tests — agents write these; tag with `# feature:` / `# spec:`.

Note: this repo keeps `CHANGELOG.md` and `CONTRIBUTING.md` at the root, not under `docs/`,
deliberately — there is no `docs/changelog.md` or `docs/contributing.md` to update.

## Coverage is computed

Never hand-author a coverage matrix. Run `python scripts/trace.py audit | report | json |
dashboard`; read `docs/trace.json` for the model.

## How to run / test / deploy

```bash
# backend
cd backend && python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 7892

# frontend
cd frontend && npm install && npm run dev   # http://localhost:1420

# test
cd backend && pytest
cd frontend && npm run typecheck
```

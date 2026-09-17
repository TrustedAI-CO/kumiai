---
id: SPEC-work-project-delete-cascade
feature: WORK-01
status: approved
---

# Deleting a project — Spec

Deleting a project is a soft delete: the project is hidden, not destroyed, so it can be
brought back. Today that promise only covers the project row itself. Its tasks and sessions
keep their own "not deleted" state and stay visible to any listing that does not go looking
for a deleted parent, and the agents the project had running keep running — still executing,
still writing files, still spending tokens against a project the human believes is gone.

This feature makes the delete cover the whole project: its children are hidden with it, and
its live agents are stopped before it disappears.

Work the agents already produced on disk is deliberately kept. Deleting a project is a
filing decision, not a demand to destroy the output.

## Behavior

| id | Given                                                                    | When                  | Then                                                                                                       |
|----|--------------------------------------------------------------------------|-----------------------|------------------------------------------------------------------------------------------------------------|
| R1 | a project with tasks and sessions that are not deleted                    | the project is deleted | those tasks and sessions are deleted too, and stop appearing anywhere the project's own children would       |
| R2 | a project whose task or session was already deleted earlier               | the project is deleted | that child keeps the moment it was originally deleted, so it is not mistaken for one the project took with it |
| R3 | a project with agents currently running                                   | the project is deleted | those agents are stopped before the project is hidden, and stop consuming budget                             |
| R4 | an agent cannot be stopped (already gone, unresponsive)                    | the project is deleted | the deletion still completes and the failure to stop is recorded, rather than leaving the project half-deleted |
| R5 | a project is deleted                                                      | the deletion completes | the project's files on disk are left exactly as they were                                                    |
| R6 | a project was deleted                                                     | a new project is created at the same path | the new project is created, rather than being refused because a hidden project still holds that path |

## Notes

R2 is what makes deletion reversible. Everything the delete hides is stamped with one shared
moment, so a later restore can tell "hidden because the project was deleted" apart from
"was already deleted before that". Without it, restoring a project would resurrect children
the human had deliberately thrown away.

R3 and R4 together fix an ordering problem that has no perfect answer: stopping an agent is
not undoable, and hiding the project is. Agents are stopped first and their failures do not
abort the delete. The reasoning is asymmetric cost — an agent left running against a deleted
project keeps spending real money and silently editing files, while an agent stopped by a
delete that then fails is merely stopped, and the human can see and restart it.

R6 is the user-visible half of a schema defect: the uniqueness rule on a project's path was
written to apply only to projects that are not deleted, but that condition was never enforced
on the database actually in use, so deleted projects keep their path reserved forever.

## Open questions

- Should deleting a project that still has running agents warn the human first, rather than
  stopping them silently? Currently specified as silent; the count is known at delete time,
  so a confirmation is possible later without changing these rules.

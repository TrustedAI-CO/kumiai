---
id: SPEC-work-project-restore
feature: WORK-02
status: approved
---

# Restoring a deleted project — Spec

A soft delete is only meaningfully "soft" if something can undo it. Today nothing can: a
deleted project is invisible to every surface, and the only way back is editing the database
by hand. This feature gives the deletion an inverse.

Restore is the exact mirror of the delete: it brings back the project and the children that
the delete took with it, and nothing else. It does not restart agents — the human decides
what should run again.

## Behavior

| id | Given                                                            | When                | Then                                                                                          |
|----|------------------------------------------------------------------|---------------------|-------------------------------------------------------------------------------------------------|
| R1 | a project that was deleted                                        | it is restored      | the project is visible again, along with the tasks and sessions that its deletion had hidden       |
| R2 | a project whose child was already deleted before the project was  | the project is restored | that child stays deleted                                                                       |
| R3 | a project that was never deleted                                  | it is restored      | the request is rejected as invalid rather than silently changing anything                          |
| R4 | a project was deleted and another project now occupies its path   | it is restored      | the restore is refused with the conflict named, rather than producing two projects on one path      |
| R5 | a project with sessions that were running when it was deleted      | it is restored      | those sessions come back stopped, not running                                                     |

## Notes

R2 is the reason the delete stamps everything it hides with one shared moment. Restore
un-hides exactly the children carrying the project's own deletion moment; a child deleted at
any other time is not the delete's to give back.

R4 exists because fixing the path-uniqueness defect makes the path free again as soon as a
project is deleted. That is correct for creating new projects and it means a restore can
arrive to find its path taken. Refusing loudly is right: the alternative is two projects
pointing at one working directory, with two agent populations editing the same files.

R5 follows from R3 of the delete spec. Agents were stopped, and stopping is not reversible.
Restoring conversation history is the promise; resuming execution is not.

## Open questions

- Should restore be reachable from the UI, or is an API-only recovery path enough? The rules
  above hold either way.
- Should a project be permanently purgeable (a real delete)? Not specified here; nothing in
  these rules assumes deleted projects live forever.

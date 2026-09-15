---
id: SPEC-<area>-<name>
feature: FEAT-1            # → functions id (the spec's only link)
status: draft             # draft → approved. The gate: audit WARNS when code
                          # implements this feature while status is still draft.
                          # A human approves: `trace.py approve SPEC-<area>-<name>`.
---

# <Feature> — Spec

Behavior only. The feature's *why* (`intent:`) and *module* (`module:`) live on its
functions row, not here.

The code that implements this feature declares ownership from its own side — put
`# feature: <functions id>` at the top of each implementing source file. The tool
collects those into the feature's file list and flags this spec **stale** if such a file is
committed after the spec.

## Behavior

Each row is one **observable rule** with a stable `Rn` id (never renumbered). Write the
outcome you can observe, in **domain terms — not the mechanism** (`returns []` / a flag /
a function name leak the implementation and rot). A test names the rule it verifies with
`# spec: SPEC-<area>-<name> Rn`.

| id | Given                | When              | Then                              |
|----|----------------------|-------------------|-----------------------------------|
| R1 | <precondition>       | <observable act>  | <observable outcome, domain terms>|

<!--
How fine? Keep it a bounded checklist (~7 rows max), not a wall:
- Rn = a rule, not a test case. One rule can be verified by many tests (the cases).
- A row earns its place only if a reviewer would approve/reject it. Visual detail →
  visual-regression; the algorithm → code / ADR. Those are not Rn.
- >7 rows = a smell: the feature is really several (split it), or you're writing cases.
-->

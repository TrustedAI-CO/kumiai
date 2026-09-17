---
id: intent
type: intent
project: KumiAI
status: signed
signed: 2026-09-15
---

# Intent — Goals

The goals the product exists to hit (the *why*). A feature points here with `intent: G1`.

> **HUMAN-owned.** Drafted from `README.md` on 2026-09-15 and **signed by the owner the same
> day** at GATE A. Agents may quote these goals and point features at them; only the owner
> edits or retires them.

## Goals

| id | goal                                                                                         |
|----|----------------------------------------------------------------------------------------------|
| G1 | A team of AI agents with distinct skills can work a project together, not one agent alone      |
| G2 | The human can see what every agent is doing, live, and step in when one needs them             |
| G3 | Work survives the session — projects, tasks and conversations resume with their context intact |
| G4 | Defining a team is a first-class authoring act: skills and agents are editable artifacts       |
| G5 | A coordinator agent can delegate work and reliably learn when it finished or failed            |

## Goal details (optional)

### G2
The failure this goal exists to prevent: an agent stops, waits for a human, and nothing
surfaces it — so the board shows a healthy team while work is actually stalled. Being able
to watch an agent think is necessary but not sufficient; the system must also make *stuck*
legible without the human going pane by pane. Success is that a human glancing at the board
can tell, in one look, which agents need them right now.

### G5
Delegation is only useful if it completes. A coordinator that spawns work and never hears
back is worse than no delegation, because it looks like progress. This goal covers the whole
round trip — the coordinator must learn the outcome whether the child succeeded, failed,
crashed, or was cancelled, and must not depend on the child agent *remembering* to report.
Non-goal: guaranteeing the child does good work. Only that its outcome is known.

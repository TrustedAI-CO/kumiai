---
id: functions
type: reference
---

# Function List — feature registry

One row per feature. Columns are **fixed in order and name**. The row carries the feature's
`module` (→ architecture.md) and `intent` (→ intent.md).

- `importance ∈ must | should | could` (MoSCoW; weights 2 / 1 / 0.5) — from the requirement
  **owner**, never invented by dev/QA. Client terms are translated once, by hand.
- `scope ∈ active | deferred` — active = scored now; deferred = reported, not scored.
- `id` = **`AREA-NN`**: uppercase area code + `-` + zero-padded number (`AI-07`, `UI-03`). The
  id lands in every `# feature:` tag and test, so it's **frozen — never reused, never renumbered**
  (retire, don't renumber). The `name` column carries the human words and may change freely.

**Areas** (fix this small list once; area = product-capability or screen-group, not module):

| area | meaning                                                  |
|------|----------------------------------------------------------|
| COORD| session coordination — spawning, delegation, notification |
| AGENT| agent execution and the CLI backends it runs on           |
| WORK | project / task / session organisation and kanban stages   |
| CAT  | agent + skill catalog and authoring                       |
| UI   | screens / surfaces                                        |
| SYS  | platform / infra                                          |

| id       | name                        | module               | intent | importance | scope  |
|----------|-----------------------------|----------------------|--------|------------|--------|
| COORD-01 | spawn records parent        | session-coordination | G5     | must       | active |
| COORD-02 | turn-end outcome recording  | session-coordination | G5     | must       | active |
| COORD-03 | parent turn-end notification| session-coordination | G5     | must       | active |
| WORK-01  | project delete cascades     | project-workspace    | G3     | must       | active |
| WORK-02  | project restore             | project-workspace    | G3     | should     | active |

> Rows are added one per feature as it is planned. Already-shipped code is not back-filled —
> that would invert the doc-first order.

The `id` is what source files point back to: put `# feature: COORD-01` at the top of each file
that implements the feature. That is the bottom-up half of traceability — it tells the tool
*where the feature lives in code*, with no central path list to keep in sync.

## Feature details (optional)

`name` is a one-line label — deliberately terse so the table scans. When a feature needs more
(what it means, edge cases, why it's `must`, client wording), add a prose block here. The tool
ignores this; it's for humans. **Prose only — no markdown tables inside a detail block.**

### AI-01
<The feature explained in full: what the user gets, the tricky context, links to the goal it
serves. The behavioral rules still live in its spec; this is the plain-language "what & why".>

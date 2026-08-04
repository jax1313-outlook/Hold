# LANE B WALKTHROUGH REPORT v1 — Manager Work Queue

Purpose: the written record of the human walkthrough required by
`LANE_B_LAUNCH_PACKAGE_v1.md` §7 ("Mike's walkthrough, run the same way
Lane A's was... approve one item and reject one item in a throwaway
sandbox") and `DISPATCH_BUILD_BLUEPRINT_v1` Part 5, gate 5. Run per the
standing procedure at `docs/reference/WALKTHROUGH_PROCEDURE_v1.md`.
Repository: `jax1313-outlook/hold`, branch `build/manager-queue`, commit
`e35a999`.

## How this walkthrough was run

Same procedure as Lane A's, by standing instruction: Mike does not have a
terminal into this remote environment, so the build session executed
every command and showed the real, unedited output at each step. This
time the real interface under test was the Flask UI itself (the thing
Mike will actually use on a tablet), so each action was a real HTTP
request against the actual running dev server (`python -m
dispatch.queue.app`), not a direct call into the Python store — the same
requests a browser would send when a human clicks a button.

## Sandbox used

A throwaway sandbox outside the git repository, built and torn down
within this session: `/home/user/mike_walkthrough_b/` (deleted after the
walkthrough completed). `tools/init_roots.py` built the standard skeleton
from a sandbox-only config, same as Lane A's.

## What was seeded

Three queue items, plus one real evidence record (via Lane A's
`EvidenceSpine.register()`) linked to one of them, so the walkthrough
would exercise both lanes working together, not the queue in isolation:

| Item | Priority | Type | Subject |
|---|---|---|---|
| 1 | today | review | Review unusual gas station receipt (linked to a registered evidence record) |
| 2 | urgent | approval | Approve Q2 IFTA worksheet |
| 3 | whenever | decision | Housekeeping: rename retired unit T-098 |

## Step 1 — The queue list, as rendered

`GET /` returned the three items correctly grouped by priority:

```
Urgent (1)   - Approve Q2 IFTA worksheet
Today (1)    - Review unusual gas station receipt
Whenever (1) - Housekeeping: rename retired unit T-098
```

## Step 2 — Item detail with a live evidence preview

`GET /items/<item-1-id>` rendered the item's metadata plus the linked
evidence record, retrieved live through Lane A's real
`EvidenceSpine.retrieve()` (hash re-verified on that call, per Lane A's
own contract):

```
pump_receipt — Flying J Travel Center, 2026-08-04 — hash verified.
```

## Step 3 — Approve one item

`POST /items/<item-1-id>/approve` with `decided_by=human:mike` and a note
returned `302` (success). Re-fetching the item confirmed:

```
Status: approved
Decided by: human:mike at 2026-08-04T13:26:00Z
Note: Confirmed against receipt image, matches unit T-104
```

## Step 4 — Reject one item

`POST /items/<item-2-id>/reject` with `decided_by=human:mike` and a note
returned `302`. Re-fetching confirmed:

```
Status: rejected
Decided by: human:mike at 2026-08-04T13:26:00Z
Note: Worksheet has wrong quarter, send back for correction
```

This satisfies the two required actions in the Definition of Done:
**approve one item, reject one item.**

## Step 5 — Decisions are final (bonus check, same spirit as Lane A's tamper demo)

Attempted `POST /items/<item-1-id>/reject` on the item just approved:

```
status 400
"cannot move ... from 'approved' to 'rejected' (allowed from: ['in_review', 'open'])"
```

The item's status was re-checked afterward and remained `approved`,
unchanged. The system refused to let an already-decided item be
overturned through the same route that decides fresh ones.

## Step 6 — Full visibility and audit trail

The full queue was read directly from storage after all decisions — all
three items still present, including the untouched third item, none
deleted or hidden:

```
1: approved  | Review unusual gas station receipt
2: rejected  | Approve Q2 IFTA worksheet
3: open      | Housekeeping: rename retired unit T-098
```

The audit trail contained one well-formed entry per real operation
(`evidence.register`, three `queue.create`, several `evidence.retrieve`
from page views, `queue.approve` with its note, `queue.reject` with its
note) — nothing missing, nothing extra, nothing from the refused
double-decide attempt (which correctly wrote no entry at all, since it
never reached the point of making a change).

## Definition of Done — status against LANE_B_LAUNCH_PACKAGE_v1 §7

| Requirement | Status |
|---|---|
| All Lane B tests green, including every negative test in §6 | Done (120/120, prior session) |
| Conformance suite (extended) green | Done (prior session) |
| Every transition writes a valid audit entry | Done — reconfirmed live in this walkthrough |
| `src/dispatch/queue/README.md` documents the store + state machine | Done (prior session) |
| `docs/lanes/B/NOTES.md` updated | Done (prior session) |
| **Mike's walkthrough**: approve one item, reject one item | **Done — this document** |
| Docs match as-built | Done — nothing observed here contradicts `MANAGER_CONSTITUTION_v1`, the launch package, or the design decisions already recorded in `NOTES.md` |
| Branch `build/manager-queue` ready for `integration` | Technically ready; final call below |

## What this report is not

Same as Lane A's: per Hard Approval Gate #7, this report is evidence for
a decision, not the decision itself. Merging `build/manager-queue` into
`integration` still requires Mike's own affirmative approval, stated in
writing, before it happens.

---

*End of LANE B WALKTHROUGH REPORT v1.*

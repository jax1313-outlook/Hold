# PREPARE THIS QUARTER WALKTHROUGH REPORT v1

Purpose: the written record of the human walkthrough required before
merge, run per the standing procedure at
`docs/reference/WALKTHROUGH_PROCEDURE_v1.md`. Repository:
`jax1313-outlook/hold`, branch `build/ifta-clerk-prepare-quarter`,
commit `ab48900`.

## How this walkthrough was run

Same procedure as every prior lane and phase: Mike does not have a
terminal into this remote environment, so the build session executed
every command and showed the real, unedited output at each step. The
real interface under test was the real running mounted server
(`python -m dispatch.shell.app`) — every request below is a real HTTP
call, not the pytest test client. Real data entered through the actual
CSV receipt-intake pipeline, the actual `tools/mileage_worksheet.py`
CLI, and the actual `rates.insert_rate()`. The failure path was covered
first, before any real data existed, then again after preparation and
submission each succeeded once.

## Sandbox used

A throwaway sandbox outside the git repository:
`/home/user/ifta_prepare_walkthrough/` (deleted after this walkthrough
completed), built with `tools/init_roots.py`.

## Step 1 — Prepare with no data at all

```
POST /ifta-clerk/prepare (quarter=2026-Q3, fuel_type=diesel) -> 400
"Could not prepare this quarter: no rate has been entered for 2026-Q3/diesel yet"
```

Clean, typed error, no crash — nothing was written (no `ifta_worksheets`
table existed at all at this point).

## Step 2 — Real data through real entry points

A real fuel CSV (Petro Stopping Center, OK, 2026-08-02, diesel, 100.0
gallons) through the real `IntakePipeline.process_drop()` — routed
cleanly. A real mileage entry (`tools/mileage_worksheet.py --unit T-104
--jurisdiction OK ... --miles 700`). A real rate
(`jurisdiction="OK", quarter="2026-Q3", fuel_type="diesel", rate=0.18`).

## Step 3 — Prepare This Quarter, for real

```
POST /ifta-clerk/prepare -> 302, Location: .../?...&prepared=1&exceptions=0
```

Independently re-verified by hand before trusting the page: `fleet_mpg
= 700 / 100 = 7.0`, inside the plausible `[4.0, 9.5]` band — correctly
zero exceptions. Confirmed via raw `sqlite3`, not this app's own code:

```
worksheet: (fleet_mpg=7.0, total_net_tax=0.0, status='draft', queue_item_id=None)
ifta_exceptions: 0
```

`queue_item_id` is `None` — Preparation did not auto-submit, exactly as
directed.

## Step 4 — Submit for Approval, then the double-submit failure path

```
POST /ifta-clerk/submit -> 302, Location: .../?...&submitted=1
```

Independently confirmed: exactly one real `approval`-type queue item,
the worksheet's `queue_item_id` now set to match it. A second
`POST /submit` immediately after:

```
-> 400
"Could not submit for approval: worksheet ... was already submitted (queue item ...)"
```

Confirmed via raw `sqlite3` again: still exactly one approval queue item
after three total submit attempts, not two.

## Step 5 — Independent confirmation through a completely separate, unmodified app

```
GET /queue/ -> "Approve IFTA worksheet 2026-Q3 (diesel): net tax 0.00"
```

The real Queue app — never touched by this branch — independently shows
the exact item this workflow created, proving the integration is real
end to end, not merely internally self-consistent.

## Definition of Done — status against the modified design

| Requirement | Status |
|---|---|
| Preparation builds + runs detectors, never submits | Done — Step 3, `queue_item_id` confirmed `None` after prepare |
| Submission is a separate, deliberate action | Done — Step 4 |
| No second approval item on repeated submit | Done — Step 4, count stayed at 1 across 3 attempts |
| Sealing stays unreachable | Done (prior session, `ast`-verified); not directly exercised live here since nothing in this branch can reach it in the first place |
| Clean failure handling, not a raw crash | Done — Steps 1 and 4's second attempt |
| Real integration with the existing Queue | Done — Step 5 |
| Automated tests, full suite green | Done (prior session) — 435/435, plus this independent live walkthrough |
| `docs/ifta-clerk/PREPARE_THIS_QUARTER_NOTES_v1.md` written | Done (prior session) |
| **Mike's walkthrough** | **Done — this document** |
| Branch `build/ifta-clerk-prepare-quarter` ready for `integration` | Technically ready; final call below |

## What this report is not

Per Hard Approval Gate #7: this is evidence for a decision, not the
decision itself. Merging `build/ifta-clerk-prepare-quarter` into
`integration` still requires Mike's own affirmative approval, stated in
writing, before it happens.

---

*End of PREPARE THIS QUARTER WALKTHROUGH REPORT v1.*

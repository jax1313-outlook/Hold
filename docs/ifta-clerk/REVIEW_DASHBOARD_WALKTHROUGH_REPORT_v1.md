# REVIEW DASHBOARD WALKTHROUGH REPORT v1

Purpose: the written record of the human walkthrough required before
merge, run per the standing procedure at
`docs/reference/WALKTHROUGH_PROCEDURE_v1.md`. Repository:
`jax1313-outlook/hold`, branch `build/ifta-clerk-review-dashboard`,
commit `88e2945`.

## How this walkthrough was run

Same procedure as every prior lane and phase: Mike does not have a
terminal into this remote environment, so the build session executed
every command and showed the real, unedited output at each step. The
real interface under test was the real running mounted server
(`python -m dispatch.shell.app`) — every request below is a real HTTP
call against the actual dev server, not the pytest test client. Real
data entered through the actual CSV receipt-intake pipeline
(`IntakePipeline.process_drop()`), the actual `tools/mileage_worksheet.py`
CLI, and the actual `rates.insert_rate()`.

## Sandbox used

A throwaway sandbox outside the git repository:
`/home/user/ifta_clerk_walkthrough/` (deleted after this walkthrough
completed), built with `tools/init_roots.py`.

## Step 1 — Shell's home page, the "primary experience" claim itself

```
GET / -> 200
<a class="card card-primary" href="/ifta-clerk/">
  <span class="label">IFTA Clerk</span>
  <span class="sublabel">Review Dashboard &rarr;</span>
```

The IFTA Clerk card renders first among the summary cards, styled
distinctly — not merely present somewhere on the page.

## Step 2 — A genuinely fresh `/ifta-clerk/`

```
GET /ifta-clerk/ -> 200
"no mileage recorded yet this quarter"
"no rate has been entered for this quarter yet"
```

Clean empty state, no crash — despite no database file having existed
before the Shell's own startup bootstrap created it.

## Step 3 — Real data through real entry points

A real fuel CSV (Love's Travel Stop, OK, 2026-08-02, diesel, 80.0
gallons) dropped into `Intake/Drop` and run through the real
`IntakePipeline.process_drop()` — routed cleanly, no quarantine. A real
mileage entry (`tools/mileage_worksheet.py --unit T-104 --jurisdiction
OK ... --miles 2000`). A real rate (`rates.insert_rate(jurisdiction="OK",
quarter="2026-Q3", fuel_type="diesel", rate=0.18)`).

## Step 4 — The real dashboard, verified by hand

```
GET /ifta-clerk/?quarter=2026-Q3&fuel_type=diesel -> 200
"ready to prepare"
CURRENT ESTIMATE — Total net tax (estimated): 0.00
Fleet MPG: 25.00 · Rate table: fixture-v1
OK: 2000.0 miles
OK: 80.0 gallons
```

Independently re-verified by hand, not trusted from the page:
`fleet_mpg = 2000 / 80 = 25.0` ✓; `net_tax = 80×0.18 − 80×0.18 = 0.00` ✓
(fuel bought matches miles driven in the same state — a correct zero,
not a missing number).

## Step 5 — The failure path

```
GET /ifta-clerk/?quarter=nonsense&fuel_type=diesel -> 400
"quarter must look like '2026-Q2', got 'nonsense'"
```

A real, typed error message, the page still renders around it (not a
raw 500).

## Step 6 — Independent verification, outside the web layer entirely

Queried the raw database file directly with Python's stdlib `sqlite3`
module, not through this app's own read code:

```
audit_log: 2       (evidence.register, receipt.process_file -- both from Step 3's real intake, not from any dashboard view)
ifta_exceptions: 0
ifta_worksheets: 0
queue_items: 0
fuel_records: [(..., 'OK', 80.0)]        -- matches the dashboard's "OK: 80.0 gallons" exactly
mileage_records: [('OK', 2000.0)]        -- matches "OK: 2000.0 miles" exactly
```

Zero governed side effects from any of the roughly ten page loads
performed in this walkthrough so far, including the failure case in
Step 5.

## Step 7 — A real Category 2 finding, categories never conflated

A real reefer-flagged `fuel_record` inserted directly (the router itself
refuses to create one; this simulates the one way it could still exist).
Reloaded the dashboard:

```
Confirmed (from a real, built worksheet): "None -- no worksheet built for this quarter yet."
Live indicators: reefer_in_propulsion (severity: critical)
```

Category 1 correctly stayed empty (no worksheet has ever been built this
quarter); Category 2 showed the real finding with its documented
severity. The two never appear in the same list.

## Definition of Done — status against the approved design

| Requirement | Status |
|---|---|
| Review Dashboard is the primary user experience (Shell links first, prominently) | Done — Step 1 |
| All seven panels assembled from real sources | Done — Steps 2, 4, 7 exercised panels 1-4, 7; panels 5-6 covered by the automated suite (15 dashboard tests) |
| Evidence First / Read-only Workspace / Human Authority / Recommendation Packages Only / no QuickBooks/DocuSign/Filing | Done — no write route exists at all; verified structurally in tests and live via Step 6's zero-side-effect confirmation |
| Category 1 vs Category 2 never conflated | Done — Step 7 |
| Clean failure handling, not a raw crash | Done — Step 5 |
| Automated tests, full suite green | Done (prior session) — 416/416, plus this independent live walkthrough |
| `docs/ifta-clerk/REVIEW_DASHBOARD_NOTES_v1.md` written | Done (prior session) |
| **Mike's walkthrough** | **Done — this document** |
| Branch `build/ifta-clerk-review-dashboard` ready for `integration` | Technically ready; final call below |

## What this report is not

Per Hard Approval Gate #7: this is evidence for a decision, not the
decision itself. Merging `build/ifta-clerk-review-dashboard` into
`integration` still requires Mike's own affirmative approval, stated in
writing, before it happens.

---

*End of REVIEW DASHBOARD WALKTHROUGH REPORT v1.*

# LANE D WALKTHROUGH REPORT v1 — Reports Layer

Purpose: the written record of the human walkthrough required by
`LANE_D_LAUNCH_PACKAGE_v1.md` §7 ("Mike's walkthrough... 'fuel today'
answered in one glance on a tablet-sized screen over LAN in sandbox; a
save-for-print round trip") and `DISPATCH_BUILD_BLUEPRINT_v1` Part 5,
gate 5. Run per the standing procedure at
`docs/reference/WALKTHROUGH_PROCEDURE_v1.md`. Repository:
`jax1313-outlook/hold`, branch `build/reports`, commit `cba9ac2`.

## How this walkthrough was run

Same procedure as Lanes A, B, and C, by standing instruction: Mike does
not have a terminal into this remote environment, so the build session
executed every command and showed the real, unedited output at each
step. As with Lane B, the real interface under test was the Flask UI
itself — every report screen and every print-queue action below is a
real HTTP request against the actual running dev server (`python -m
dispatch.reports.app`), not a direct call into `queries.py`. The data
behind those screens was produced by the lane's own upstream chain, not
hand-inserted: a real fuel purchase went through Lane C's actual intake
pipeline, and a real IFTA worksheet was built with Lane C's actual
`WorksheetEngine`, before Reports ever queried either.

## Sandbox used

A throwaway sandbox outside the git repository, built and torn down
within this session: `/home/user/mike_walkthrough_d/` (deleted after the
walkthrough completed). `tools/init_roots.py` and `tools/seed_library.py`
built the standard skeleton and installed the three report templates,
same as every prior lane's sandbox.

## Step 1 — A real fuel purchase, through the real intake pipeline

A fuel-card CSV export (`Love's Travel Stop`, TX, 96.0 gallons, $412.80,
dated today) was dropped into `Intake/Drop` and run through
`process_drop()` — Lane C's real code, not a Reports-side shortcut.

First attempt was malformed (the `TOTAL` marker row's declared total
landed in the wrong column) and was correctly quarantined rather than
silently accepted:

```
{"quarantined_files": [{"file": "fuel_card_export.csv", "reason": "could not convert string to float: ''", ...}]}
```

That quarantine is itself a real instance of this lane's designed
failure path showing up unplanned — a genuinely malformed drop file was
refused, not guessed at, and (see Step 6) left a real audit trail and
queue item rather than vanishing. The file was corrected and re-dropped;
the second attempt processed cleanly:

```
{"processed": [{"file": "fuel_card_export.csv", "evidence_record_id": "01KZ6QZ1YJ..."}],
 "routed": [{"fuel_record_id": "01KZ6QZ1YN...", "expense_record_id": "01KZ6QZ1YN..."}]}
```

## Step 2 — Real mileage and a real draft IFTA worksheet

1,350 TX miles for 2026-Q3 were entered via `tools/mileage_worksheet.py`
(the same tool Lane C's walkthrough used), a fixture TX/2026-Q3/diesel
rate was inserted (`source_version: "fixture-v1"`, never a real
published rate), and a draft worksheet was built with the real
`WorksheetEngine.build()`:

```
fleet_mpg: 14.0625   (1350 miles / 96.0 gallons)
TX line:   miles=1350.0, taxable_gallons=96.0, tax_paid_gallons=96.0, net_tax=0.00
status: draft
```

## Step 3 — The homepage on a brand-new database

`GET /` was hit before anything had ever been saved to the print queue —
deliberately, since this is exactly the state that 500'd earlier in this
build session (`print_queue` didn't exist yet; see `NOTES.md`). It
returned `200`, rendered cleanly, with no recents chips:

```
HTTP status: 200
<title>Reports</title> ... Report Type / Date Range form, no <nav class="recents">
```

## Step 4 — "Fuel today," answered in one glance

`GET /run?report_type=fuel_spend&date_range=today`:

```
Total Fuel Spend: $412.80
Gallons: 96.0
By State: TX  $412.80  96.0
```

This is the Definition of Done's headline requirement, against real data
that went through the real intake pipeline earlier in this same session.

## Step 5 — IFTA Position: the real worksheet, and the designed "no data" failure path

For the quarter with a real worksheet (`GET /run?report_type=ifta_position`,
custom range landing in 2026-Q3):

```
Estimated Net Tax: $0.00   (read exactly as stored — fleet_mpg 14.0625, TX net_tax 0.00)
Exceptions: 0
Prepared — estimate, not filed
```

For a quarter with no worksheet at all (`custom_from=2026-01-01,
custom_to=2026-01-31`, deliberately chosen to hit the failure path
rather than wait for one to occur by accident):

```
HTTP status: 200
"No data behind this report yet for Custom — nothing to show, and nothing fabricated."
```

No crash, no fabricated zero standing in for a real answer — the
behavior `REPORTS_CHARTER_v1.md` requires by name.

## Step 6 — Save For Printing, full round trip

`POST /save` (Fuel Spend, Today) → `302` → `/print-queue` shows one
`queued` entry. Its archived snapshot was independently verified two
ways: read through the app (`GET /print-queue/<id>/view`, showing the
same $412.80/96.0 answer plus an "immutable archive copy" stamp) **and**
found directly on disk outside the app's own code:

```
/home/user/mike_walkthrough_d/Archive/ReportSnapshots/2026/01KZ6R0BYF22XAANHD0F4Y3BVX.html
```

`POST .../mark-printed` then `POST .../clear` transitioned the entry to
`printed` then `cleared` — both `302`s, both reflected on the print-queue
page (`status-cleared`).

## Step 7 — Attempting to delete a print_queue row directly, outside the app

The clearest version of "cover the failure path" for this lane: a raw
`sqlite3` connection (not the app, not `ReportSnapshotWriter`) attempted
`DELETE FROM print_queue WHERE 1=1` directly against the database file:

```
DELETE REJECTED: print_queue entries are cleared via status, never deleted
```

Rejected by the trigger itself, not by application code that could be
bypassed. Re-checked afterward: the cleared entry was still present
(`status-cleared`) and its archived HTML file on disk was untouched by
either the clear or the rejected delete attempt.

## Step 8 — Full audit trail

Every real operation across the whole walkthrough, read directly from
`audit_log`, in order, nothing missing and nothing extra:

```
librarian  | evidence.register              | completed   (the first, malformed CSV drop)
manager    | queue.create                   | completed   (quarantine -> real queue item)
receipt    | receipt.process_file           | quarantined
librarian  | evidence.register              | completed   (the corrected CSV drop)
receipt    | receipt.process_file           | completed
reports    | reports.save_snapshot          | completed
reports    | reports.mark_printed           | completed
reports    | reports.clear_print_queue_item | completed
```

8 entries, 8 real operations. The rejected direct `DELETE` in Step 7
correctly wrote nothing — it never reached the point of making a change.

## Definition of Done — status against LANE_D_LAUNCH_PACKAGE_v1 §7

| Requirement | Status |
|---|---|
| All Lane D tests green (85 tests: dates, templates, rendering determinism, query correctness + fidelity, IFTA display-only, read-only enforcement, no-tax-math/no-DELETE-SQL grep guards, snapshot writer, incomplete-data handling, fixture conformance, Flask routes) | Done (prior session) |
| Full repo suite green | Done — 298/298 (prior session) |
| Fixtures built from real Lane A/C pipeline code, not hand-typed rows | Done (prior session) — and reused live in this walkthrough |
| `src/dispatch/reports/README.md` documents the read-only/single-writer split, templates-as-data, and the two bugs this session found | Done (prior session) |
| `docs/lanes/D/NOTES.md` updated | Done (prior session) |
| **Mike's walkthrough**: "fuel today" in one glance, save-for-print round trip | **Done — this document** |
| Failure path demonstrated, not just the happy path | Done — malformed CSV quarantine (Step 1), no-worksheet "no data" page (Step 5), direct DELETE rejection (Step 7) |
| Docs match as-built | Done — nothing observed here contradicts `REPORTS_CHARTER_v1.md`, the launch package, or `NOTES.md` |
| Deferred final report fidelity gate | Still explicitly open — this walkthrough used a fresh sandbox's real pipeline output, not `integration`'s accumulated real data; `NOTES.md` still lists this as the open item it always was |
| Branch `build/reports` ready for `integration` | Technically ready; final call below |

## What this report is not

Same as every prior lane's: per Hard Approval Gate #7, this report is
evidence for a decision, not the decision itself. Merging
`build/reports` into `integration` still requires Mike's own affirmative
approval, stated in writing, before it happens.

---

*End of LANE D WALKTHROUGH REPORT v1.*

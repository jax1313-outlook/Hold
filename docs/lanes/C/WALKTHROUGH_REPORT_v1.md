# LANE C WALKTHROUGH REPORT v1 — Receipt → IFTA Chain

Purpose: the written record of the human walkthrough required by
`LANE_C_LAUNCH_PACKAGE_v1.md` §7 ("drop one real (or realistic fixture)
document in a sandbox, watch it register → extract → validate → route
into real Fuel/Expense records, and produce a draft IFTA worksheet from
fixture rate data + manually entered mileage") and
`DISPATCH_BUILD_BLUEPRINT_v1` Part 5, gate 5. Run per the standing
procedure at `docs/reference/WALKTHROUGH_PROCEDURE_v1.md`.
Repository: `jax1313-outlook/hold`, branch `build/receipt-ifta`, commit
`34c7b65`.

## How this walkthrough was run

Same procedure as Lanes A and B: Mike does not have a terminal into this
remote environment, so the build session executed every command and
showed the real, unedited output at each step. This lane's real interface
is deeper than A or B's (a multi-stage pipeline plus a separate
computation engine), so the walkthrough exercises both halves — the
receipt chain and the IFTA chain — as one connected sandbox session, the
same fleet and quarter carried through both.

## Sandbox used

A throwaway sandbox outside the git repository, built and torn down
within this session: `/home/user/mike_walkthrough_c/` (deleted after the
walkthrough completed). `tools/init_roots.py` built the standard skeleton
from a sandbox-only config, same as Lanes A and B's.

## Part 1 — Receipt intake, extraction, routing, and quarantine

Two documents were dropped into `Intake\Drop`:

| File | Content |
|---|---|
| `week1_export.csv` | A clean CSV export: one diesel fuel line, one meal line, a declared total |
| `unreadable_scan_notes.csv` | One line with no `vendor_name` — a required field |

`process_drop()` was run once against both:

```
processed:   week1_export.csv -> evidence registered
quarantined: unreadable_scan_notes.csv -> "row missing required field(s): ['vendor_name']"
routed:      1 FuelRecord + ExpenseRecord (fuel, cross-linked)
             1 ExpenseRecord (meals)
```

Independently confirmed on the filesystem: `week1_export.csv` ended up in
`Intake\Processing`; `unreadable_scan_notes.csv` ended up in
`Intake\Quarantine` — **and it was still archived first** (it has an
`evidence_record_id`) before being quarantined, matching contract 1.4's
"archive before extraction" rule even on a failure path. An `exception`
queue item was raised for it, `status: open`.

The routed records were read directly from the database:

```
fuel_records:    Flying J Travel Center, TX, 87.5 gal, $350.00
expense_records: Flying J Travel Center, category=fuel,   $350.00, fuel_record_id set
                 Truck Stop Diner,       category=meals,  $18.50,  fuel_record_id NULL
```

Jurisdiction (`TX`) was derived from the vendor address automatically,
not entered manually. The fuel line produced *both* records, cross-linked
by ID in both directions; the meal line produced an expense record only.

## Part 2 — Safety check: reefer fuel can never become a FuelRecord

A line categorized `fuel` but flagged `tractor_or_reefer: reefer` (the
one way a classification bug could slip a reefer purchase into IFTA
propulsion gallons) was submitted directly to the router:

```
Correctly refused: a reefer-flagged line was categorized 'fuel' instead
of 'reefer_fuel' -- refusing to create a FuelRecord for it
Reefer-flagged rows in fuel_records (should be 0): 0
```

## Part 3 — Mileage entry and the draft IFTA worksheet

Mileage was entered via `tools/mileage_worksheet.py` (manual entry, the
v1 reality per the mileage contract): unit `T-104`, jurisdiction `TX`,
1400 miles for 2026-Q3, entered by `human:mike`.

A **fixture** rate was inserted for TX/2026-Q3/diesel — tagged
`source_version: "fixture-v1"`, not a real published rate (see
`library_seed/RateTables/README.md`) — and the draft worksheet was built:

```
fleet_mpg: 16.0   (1400 miles / 87.5 gallons -- the one fuel purchase from Part 1)
TX line:   miles=1400, taxable_gallons=87.5, tax_paid_gallons=87.5, net_tax=0.00
```

## Part 4 — Exception detection

All ten detectors were run against the draft worksheet:

```
fleet_mpg_out_of_band: fleet_mpg 16.00 outside plausible range [4.0, 9.5]
```

Correctly flagged — a single fuel purchase and one mileage entry produces
an implausible fleet MPG, and the system raised it rather than silently
accepting it. A new `urgent` exception queue item exists for it.

## Part 5 — Approval-gated seal

The worksheet was submitted for approval (a new `approval` queue item,
subject: *"Approve IFTA worksheet 2026-Q3 (diesel): net tax 0.00"*),
approved with a note acknowledging the MPG flag, and sealed:

```
status: sealed
sealed_at: 2026-08-04T15:06:00Z
```

The bundle (worksheet + lines + who approved it) was independently
confirmed on disk at `ARCHIVE\IFTA\2026-Q3\<worksheet_id>.json`.

## Part 6 — Full visibility and audit trail

The queue at the end of the walkthrough held all three items it should —
none hidden, none deleted:

```
exception  | open     | Intake failure: unreadable_scan_notes.csv
exception  | open     | IFTA exception (fleet_mpg_out_of_band): ...
approval   | approved | Approve IFTA worksheet 2026-Q3 (diesel): net tax 0.00
```

Nine audit entries were written across the walkthrough — `librarian`
(evidence register/retrieve), `receipt` (process_file), and `manager`
(queue create/approve) — one per real operation, nothing missing.

## Definition of Done — status against LANE_C_LAUNCH_PACKAGE_v1 §7

| Requirement | Status |
|---|---|
| All Lane C tests green, including every negative test in §6 | Done (213/213, prior session) |
| Conformance suite (extended) green | Done (prior session) |
| Every operation writes a valid audit entry | Done — reconfirmed live in this walkthrough |
| `src/dispatch/receipt/README.md` and `src/dispatch/ifta/README.md` written | Done (prior session) |
| `docs/lanes/C/NOTES.md` updated, Trade Memory the only parked item | Done (prior session) |
| **Mike's walkthrough**: register/extract/validate/route + draft worksheet | **Done — this document** |
| Docs match as-built | Done — nothing observed here contradicts `RECEIPT_CONSTITUTION_v1`, `IFTA_CONSTITUTION_v1`, the launch package, or `NOTES.md`'s recorded design decisions |
| Branch `build/receipt-ifta` ready for `integration` | Technically ready; final call below |

**Not required for this lane's merge, unchanged from before this
walkthrough**: real IFTA per-jurisdiction rate data — this walkthrough
used clearly-tagged fixture rates throughout, same as the automated
golden-quarter test. That gap blocks the golden-regression *gate* being
callable against real numbers, not this lane's merge.

## What this report is not

Same as Lanes A and B: per Hard Approval Gate #7, this report is evidence
for a decision, not the decision itself. Merging `build/receipt-ifta`
into `integration` still requires Mike's own affirmative approval, stated
in writing, before it happens.

---

*End of LANE C WALKTHROUGH REPORT v1.*

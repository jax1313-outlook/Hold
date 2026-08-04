# LANE D FIDELITY GATE REPORT v1 — Deferred Final Report Fidelity

Purpose: the written record of closing the deferred gate named in
`REPORTS_CHARTER_v1.md` §"Deferred gate" and
`LANE_D_LAUNCH_PACKAGE_v1.md` §7: "Final report fidelity — every
displayed total equals independent SQL arithmetic — re-run against
**real** Lane C output on `integration`... Fixture-based fidelity in Lane
D's own gate is necessary but not sufficient." Run at Mike's explicit
instruction, after Lane D's merge, against `integration` at commit
`44493fe`.

## Why this is separate from Lane D's own build-session fidelity test

Lane D's own test suite (`tests/lane_d/test_queries.py`) already checks
displayed totals against independent SQL, but on fixtures this lane's own
build session constructed — even though those fixtures were built by
running Lane A's/Lane C's real code (`tests/fixtures/README.md`), the
charter is explicit that this is "necessary but not sufficient": a
build session checking its own fixtures can't rule out a shared blind
spot between the fixture and the query it's checking. This gate re-runs
the same discipline on `integration`'s actual merged codebase, with a
dataset built independently of Lane D's own fixture design, and — for
IFTA specifically — with the check strengthened to re-derive the numbers
from computation spec 3.5 from scratch rather than only comparing
against the worksheet engine's own stored output.

## Sandbox and dataset

A throwaway sandbox outside the repository (`/home/user/fidelity_gate_d/`,
deleted after this gate ran), built against `integration` at `44493fe`
(Lane D's merge commit) using `tools/init_roots.py` / `seed_library.py`,
same as every walkthrough. The dataset was deliberately larger and more
varied than Lane D's own fixtures or its walkthrough's single purchase,
to actually stress group-by/breakdown logic:

- **8 fuel purchases** across **3 jurisdictions** (TX, MO, OK), **2 fuel
  types** (diesel, gasoline), including one purchase in **liters**
  (`gallons_normalized` fidelity for the unit conversion) — run through
  the real `process_drop()` intake pipeline from a single CSV export,
  all 14 lines routing cleanly (0 quarantined).
- **6 standalone expense lines** across **5 categories** (meals ×2,
  tolls, truck_wash, parts_maintenance, parking).
- **Real mileage** entered via `tools/mileage_worksheet.py` for TX
  (2,200 mi), MO (950 mi), OK (780 mi), 2026-Q3.
- A **real draft IFTA worksheet** built with the real
  `WorksheetEngine.build()` (fixture TX/MO/OK diesel rates,
  `source_version: "fixture-v1"`) — fleet_mpg and net_tax computed by
  Lane C's real code, not fabricated for this gate.

## The check

A standalone script (not part of the pytest suite, run live) queried the
real `dispatch.reports.queries` functions through the real `mode=ro`
connection, then independently recomputed the same numbers with
separately-written SQL/Python that never imports `dispatch.reports.queries`
— see the full methodology and output captured below. 33 individual
value comparisons were made; all 33 passed.

### Fuel Spend, full quarter, no filters

| Value | Displayed | Independent |
|---|---|---|
| total_amount | $2,584.75 | $2,584.75 |
| total_gallons | 640.2946 | 640.2946 |
| TX breakdown | $1,373.75 / 345.0 gal | $1,373.75 / 345.0 gal |
| MO breakdown | $626.00 / 150.0 gal | $626.00 / 150.0 gal |
| OK breakdown | $585.00 / 145.2946 gal | $585.00 / 145.2946 gal |

(OK's 145.2946 gallons is 550 liters × 0.264172 — the unit-conversion
fidelity check, not a round number, deliberately.)

### Fuel Spend, filtered by jurisdiction=TX

Displayed $1,373.75 / 345.0 gal across 4 rows (3 diesel + 1 gasoline, all
TX) — matched independent SQL filtered the same way.

### Expense Summary, full quarter, category breakdown

Displayed total $3,001.25 across 6 categories (`fuel` $2,584.75 — the
D1 dual-record fuel-linked expense rows, not the 6 standalone lines
alone — plus `meals` $41.25, `parts_maintenance` $310.25, `truck_wash`
$45.00, `tolls` $12.00, `parking` $8.00) — every category total matched
independent `GROUP BY` arithmetic over the same 14 rows.

### Expense Summary, category=meals drill-down

2 line items, $18.50 and $22.75, $41.25 total — matched independently
queried rows in the same order.

### IFTA Position — the strongest check

Displayed values matched **both** the `WorksheetEngine.build()` return
(ground truth at build time) **and** an independent re-derivation of
computation spec 3.5 from raw `mileage_records`/`fuel_records`, done from
scratch with no import of anything under `dispatch.ifta`:

| Value | Displayed | Independent (spec 3.5 from scratch) |
|---|---|---|
| fleet_mpg | 6.33569919841314 | 6.33569919841314 |
| net_tax[TX] | $4.447741475826987 | $4.447741475826987 |
| net_tax[MO] | −$0.010642417302790363 | −$0.010642417302790363 |
| net_tax[OK] | −$3.9928850381679375 | −$3.9928850381679375 |
| total_net_tax | $0.44421402035625945 | $0.44421402035625945 |

This is the check the charter's "necessary but not sufficient" language
was pointing at: even if `queries.py` and `WorksheetEngine` shared a bug,
recomputing miles/gallons → fleet_mpg → taxable_gallons → net_tax from
the raw tables independently would not reproduce it. It didn't.

### IFTA Position, no worksheet for a quarter (2026-Q1)

`ifta_position_query` returned `None`; an independent `COUNT(*)` against
`ifta_worksheets WHERE quarter = '2026-Q1'` confirmed 0 rows — the "no
data" contract held for a genuinely nonexistent quarter, not just the
walkthrough's example.

### Rendered HTML, not just the Python dict

The actual `render_answer_html()` output was checked to contain the
exact displayed strings (`$2,584.75`, `$0.44`) — confirmed on both the
Fuel Spend and IFTA Position templates, and separately reconfirmed live
against the real Flask dev server via `curl`.

## Full check log

```
CHECK 1 -- Fuel Spend, full quarter, no filters:            8/8 PASS
CHECK 2 -- Fuel Spend, filtered by jurisdiction=TX:          3/3 PASS
CHECK 3 -- Expense Summary, full quarter, category breakdown: 7/7 PASS
CHECK 4 -- Expense Summary, category=meals drill-down:        4/4 PASS
CHECK 5 -- IFTA Position, displayed vs. ground truth
           and independently re-derived spec 3.5:           20/20 PASS
CHECK 6 -- IFTA Position, no-data quarter:                    1/1 PASS
CHECK 7 -- Rendered HTML contains exact displayed values:     2/2 PASS

GATE RESULT: PASS -- every displayed value matched independent
arithmetic, run against real Lane C output.
```

(Two inline code comments in the check script under-counted expected row
totals by one each — TX's gasoline purchase and one fuel-linked expense
row were left out of the comment's own arithmetic, not the assertions.
Noted here for transparency; it was a comment bug in the verification
script, not a discrepancy the gate found, and every actual assertion in
the log above passed against the real counts.)

## Made permanent

The single strongest new check from this gate — IFTA's fleet_mpg/net_tax
independently re-derived from spec 3.5 against raw tables, not just
compared to the stored worksheet value — plus a genuinely
3-jurisdiction/6-category fuel and expense fidelity check, are now
`tests/lane_d/test_fidelity_gate.py`, part of the standing suite (302
tests total, all green). This keeps the gate's rigor checked on every
future change, not just this one-time run.

## Definition of Done — status

| Requirement (`REPORTS_CHARTER_v1.md` deferred gate) | Status |
|---|---|
| Re-run against real Lane C output on `integration`, not just fixtures | Done — this document, `integration` @ `44493fe` |
| Every displayed total equals independent SQL arithmetic | Done — 33/33 checks passed |
| Never silently skipped | Done — was open in `docs/lanes/D/NOTES.md` since the merge; closed here, explicitly, with the full check log |

## What this report is not

Same as every walkthrough report before it: per Hard Approval Gate #7,
this is evidence that the gate was run and passed — it does not itself
constitute or replace Mike's decision about what to do with that result.

---

*End of LANE D FIDELITY GATE REPORT v1.*

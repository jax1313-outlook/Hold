# WORKSHEET PREVIEW MODE WALKTHROUGH REPORT v1

Purpose: the written record of the human walkthrough required before
merge, run per the standing procedure at
`docs/reference/WALKTHROUGH_PROCEDURE_v1.md`. Repository:
`jax1313-outlook/hold`, branch `build/ifta-worksheet-preview`, commit
`7d9b45b`.

## How this walkthrough was run

Same procedure as every prior lane and phase: Mike does not have a
terminal into this remote environment, so the build session executed
every command and showed the real, unedited output at each step, waiting
for acknowledgment between steps. The real interface under test was
`dispatch.ifta.worksheet.preview()` itself — no demo mode, no mocked
data. Every fuel/mileage/rate record used was created through the
project's own real entry points: the actual CSV receipt-intake pipeline
(`IntakePipeline.process_drop()`), the actual `tools/mileage_worksheet.py`
CLI, and the actual `rates.insert_rate()`.

## Sandbox used

A throwaway sandbox outside the git repository:
`/home/user/ifta_preview_walkthrough/` (not reused from any prior
walkthrough). `tools/init_roots.py` built the standard OPERATIONS/
LIBRARY/ARCHIVE skeleton.

## Step 1 — A genuinely fresh database, `preview()` before anything exists

Confirmed no database file existed yet (`os.path.exists` → `False`), then
called `bootstrap()` (the same call every real entry point makes) and
immediately `preview()` against the resulting empty database:

```
InsufficientDataError: no rate table exists yet for 'fixture-v1' -- no
rate has ever been entered against this database
```

Clean, typed error — not the raw `sqlite3.OperationalError` a genuinely
fresh install used to produce (the bug class documented in
`docs/ifta-ui/NOTES.md` on the unmerged `build/ifta-ui` branch, fixed at
the source as part of this change).

## Step 2 — Real data through real entry points

- `tools/mileage_worksheet.py --unit T-104 --jurisdiction TX ... --miles 1500` →
  a real `mileage_record_id`.
- A real fuel-card CSV (`Flying J Travel Center, ... TX 79101, 2026-05-10,
  diesel, 100.0 gallons, $400.00`) dropped into `Intake/Drop` and run
  through the real `IntakePipeline.process_drop()`:
  ```
  {"processed": [...], "quarantined_files": [], "quarantined_lines": [],
   "routed": [{"fuel_record_id": "...", "expense_record_id": "..."}]}
  ```
  No quarantine — the router derived jurisdiction `TX` from the vendor
  address itself, same as any real receipt.
- A second mileage record, `OK`, 500 miles — to exercise real
  multi-jurisdiction math rather than a degenerate single-state case.
- Two real rates via `rates.insert_rate()`: TX at `0.20`, OK at `0.18`,
  both `source_version="fixture-v1"`.

## Step 3 — `preview()` against real accumulated data, verified by hand

```json
{
  "status": "preview", "is_preview": true,
  "fleet_mpg": 20.0, "total_net_tax": -0.5,
  "lines": [
    {"jurisdiction": "OK", "miles": 500.0, "taxable_gallons": 25.0, "tax_paid_gallons": 0.0, "net_tax": 4.5},
    {"jurisdiction": "TX", "miles": 1500.0, "taxable_gallons": 75.0, "tax_paid_gallons": 100.0, "net_tax": -5.0}
  ]
}
```

Independently re-verified by hand, not trusted from the printed output:

- `fleet_mpg = (1500 + 500) / 100 = 20.0` ✓
- `taxable_gallons_TX = 1500 / 20.0 = 75.0` ✓, `taxable_gallons_OK = 500 / 20.0 = 25.0` ✓
- `net_tax_TX = 75×0.20 − 100×0.20 = -5.0` ✓ (TX bought more fuel than it drove — a real credit)
- `net_tax_OK = 25×0.18 − 0×0.18 = 4.5` ✓
- `total_net_tax = -5.0 + 4.5 = -0.5` ✓

All five figures matched exactly. Then, independently of this project's
own `get()`/`build()` code, queried the raw database file with Python's
stdlib `sqlite3` module directly:

```
ifta_worksheets rows: 0
ifta_worksheet_lines rows: 0
```

Zero rows, confirmed outside the code path under test.

## Step 4 — The failure path, not just the happy path

Two designed failure behaviors, demonstrated firing for real:

```
--- a rate_table_version that was never entered ---
MissingRateError: no rate found for jurisdiction(s) ['OK', 'TX'] in
2026-Q2/diesel/'nonexistent-v9' -- refusing to fabricate one

--- attempting a write through the same connection preview() was given ---
OperationalError: attempt to write a readonly database
```

The second is the structural guarantee, not a convention: the connection
`preview()` receives rejects writes at the SQLite layer itself, against
any table, regardless of what the calling code intends.

## Step 5 — Real `build()` for direct comparison, then `preview()` again

`WorksheetEngine.build()` against the identical data produced identical
numbers (`fleet_mpg=20.0`, `total_net_tax=-0.5`, matching per-jurisdiction
lines), plus a real `ifta_worksheet_id`, `created_at`, `status: "draft"` —
since this one actually persists. Independently confirmed via raw
`sqlite3`:

```
ifta_worksheets rows: 1
ifta_worksheet_lines rows: 2
```

Called `preview()` one more time, after the real worksheet already
existed. It returned the same numbers, still carried no
`ifta_worksheet_id`, and — confirmed independently again — left the row
counts unchanged:

```
ifta_worksheets rows: 1
ifta_worksheet_lines rows: 2
```

A `preview()` call never adds a row, whether run before or after a real
`build()`, and its result never collides with — or could be confused
for — the one real worksheet that exists.

## Definition of Done — status against the six approved conditions

| Condition | Status |
|---|---|
| 1. No database writes | Done — demonstrated live: the connection itself rejects a write attempt |
| 2. No worksheet IDs | Done — every `preview()` result in this walkthrough carried no `ifta_worksheet_id` |
| 3. No audit status changes | Done — row counts independently confirmed unchanged across every `preview()` call |
| 4. No approval path activation | Done (prior session, `ast`-verified) — not directly re-exercised live here since there's no queue item to observe *not* appearing; static proof stands |
| 5. Clearly labeled PREVIEW | Done — every result carried `"status": "preview"`, `"is_preview": true` |
| 6. Cannot be mistaken for a filed worksheet | Done — compared directly against a real `build()` result in Step 5; no shared identity |
| Automated tests, full suite green | Done (prior session) — 370/370, plus this independent live walkthrough |
| `docs/ifta-clerk/WORKSHEET_PREVIEW_MODE_NOTES_v1.md` written | Done (prior session) |
| **Mike's walkthrough** | **Done — this document** |
| Branch `build/ifta-worksheet-preview` ready for `integration` | Technically ready; final call below |

## What this report is not

Per Hard Approval Gate #7: this is evidence for a decision, not the
decision itself. Merging `build/ifta-worksheet-preview` into
`integration` still requires Mike's own affirmative approval, stated in
writing, before it happens.

---

*End of WORKSHEET PREVIEW MODE WALKTHROUGH REPORT v1.*

# Lane D — Reports Layer — NOTES

Branch: `build/reports`. Packet: `docs/reference/DISPATCH_MATRIX_EXECUTION_PACKAGE_v1.md` Packet D.
Merges last.

Update this file at the end of every Lane D session. Do not delete prior
entries — append.

## Session 1 (2026-08-04) — full build

## Built

- `src/dispatch/reports/readonly.py` — `open_read_only()`, a genuine
  SQLite `mode=ro` connection, deliberately duplicated (not imported)
  from `dispatch.ifta.readonly` per the launch package's import boundary.
- `src/dispatch/reports/db.py` — `print_queue` schema + its
  `trg_print_queue_no_delete` trigger. `create_app()` now installs this
  schema eagerly at startup (see Flagged below).
- `src/dispatch/reports/dates.py` — the six date-range presets +
  `quarter_label_for_date()`.
- `src/dispatch/reports/queries.py` — `fuel_spend_query`,
  `expense_summary_query` (with category drill-down), `ifta_position_query`
  (reads `fleet_mpg`/`net_tax` exactly as stored, never recomputes),
  `pending_review_count`. All three report queries now tolerate their
  backing table not existing yet (see Flagged below).
- `src/dispatch/reports/templates_engine.py` + `src/dispatch/reports/rendering.py`
  — versioned JSON template loading and the one HTML-rendering code path
  shared by the live fragment and the immutable snapshot.
- `library_seed/Templates/Reports/{fuel_spend,expense_summary,ifta_position}.v1.json`
  — the three report templates.
- `src/dispatch/reports/snapshot.py` — `ReportSnapshotWriter`, the one
  writer this lane is allowed. `clear()`/`mark_printed()` are status
  transitions; `print_queue` never gets a DELETE code path.
- `src/dispatch/reports/app.py` + `templates/*.html` + `static/style.css`
  — the Flask UI: Recents chips, Report Type/Date Range/Filters, one
  answer, Save For Printing, print queue.
- `tests/lane_d/` — 85 tests: date presets, template loading, rendering
  determinism, query correctness + fidelity vs. independent SQL, IFTA
  display-only fidelity, read-only-connection enforcement (multiple
  tables), no-tax-math and no-DELETE-SQL static grep guards, snapshot
  writer (file + queue row + audit entry + status transitions + trigger
  rejection), incomplete-data handling, fixture conformance against the
  frozen `fuel_record`/`expense_record` schemas, and full Flask route
  coverage.
- `tests/lane_d/conftest.py` / `tests/fixtures/README.md` — fixtures
  built by actually running Lane A's `EvidenceSpine.register()` and Lane
  C's `Router.route_line()` / `WorksheetEngine.build()`, not hand-typed
  rows — see that README for why, and for why this substantially de-risks
  (without replacing) the deferred fidelity gate below.

## Flagged (held decisions / open questions encountered)

- **Two real bugs found only by manual smoke-testing, not the automated
  suite** — the same pattern Lanes B and C already logged. Both are now
  fixed and covered by regression tests:
  1. `print_queue` is created lazily by `ReportSnapshotWriter.__init__`,
     but `/` calls `recent_reports()` on the read-only connection
     regardless of whether anyone has ever saved a report. On a brand-new
     database, the very first page load 500'd with `no such table:
     print_queue`. Fixed by having `create_app()` install that schema
     once, eagerly, at startup — the same guarantee `bootstrap()` gives
     Lane A's tables. See `app.py`'s docstring/comment and `README.md`.
  2. `fuel_records`/`expense_records` (Lane C's receipt side) and
     `ifta_worksheets` (Lane C's IFTA side) are each created lazily by
     that lane's own code the first time it actually runs something —
     not by `bootstrap()`. On a fresh install where no receipt has been
     processed or no worksheet built yet, every report query crashed
     with `no such table: ...` instead of showing "no data yet." Fixed
     with a `_table_exists()` guard in `queries.py`: a missing table now
     reads exactly like an empty result (zero totals for Fuel Spend/
     Expense Summary, `None` for IFTA Position, same as the already-
     correct "no worksheet for this quarter" path).
  Both were caught by actually running `python -m dispatch.reports.app`
  against a real sandbox seeded through the real intake pipeline
  (`process_drop`), `tools/mileage_worksheet.py`, and a real
  `WorksheetEngine.build()` call, then hitting every route with `curl` —
  not by the 85 automated tests, which all passed against the buggy code
  first. This is now the fourth lane in a row where the manual
  smoke-test step caught something the suite didn't.
- **IFTA Position ignores the Truck/State filters in v1** (documented
  already in `README.md` and `app.py`'s `_compute()`): filtering
  `ifta_worksheet_lines` without also re-deriving `total_net_tax` would
  make the big number and the breakdown table visibly disagree — exactly
  the "divergent numbers" failure the charter calls out. Not silently
  dropped: the filter inputs are simply not passed through for this one
  report type.
- Decision D3 ("expense_summary blocked on #3") was approved 2026-08-04
  per `docs/decisions/DECISION_LOG.md` before this session started, so
  Expense Summary was built along with the other two report types with
  no further gating needed.

## Deliberately Not Built

- No fourth report type — the launch package's "add a report type is a
  template file + a fixture" design is implemented and exercised only by
  the three in-scope reports; nothing else has been added to prove it out
  further.
- No pagination/sorting on the print queue or on breakdown/drill-down
  tables — REPORTS_CHARTER_v1.md's "every dropdown removed is a gift to
  the person in the truck" argues against adding one until real usage
  shows the list is too long to read.
- No caching layer for repeated identical queries — the charter's
  determinism requirement is about identical bytes out, not about
  response time, and query volume through this lane doesn't currently
  justify one.

## Deferred gate — CLOSED 2026-08-04

Final report fidelity gate (validation gate 6) was deferred to
`integration`, to be re-run against real Lane C data before merge 5. Not
skipped — this session's fixtures already ran through Lane A's/Lane C's
real code (see `tests/fixtures/README.md`), which substantially de-risked
this gate, but the data itself was still synthetic (not Mike's actual
receipts), so it stayed open until re-checked on `integration`.

Per Mike's instruction after the merge, it was run: a 3-jurisdiction
(TX/MO/OK), 2-fuel-type, 6-category dataset was built through the real
`process_drop()` intake pipeline and a real `WorksheetEngine.build()` on
`integration` @ `44493fe`, and every value the three report types display
was independently recomputed — for IFTA, all the way back to raw
`mileage_records`/`fuel_records` per computation spec 3.5, not just
compared against the stored worksheet. 33/33 checks passed; full detail
in `docs/lanes/D/FIDELITY_GATE_REPORT_v1.md`. The strongest of those
checks (IFTA's independent spec-3.5 re-derivation, plus the
multi-jurisdiction fuel/expense breakdown fidelity) is now a permanent
regression, `tests/lane_d/test_fidelity_gate.py` — 302 tests green across
the repo with it included. Data used for this gate was still
sandbox-built (not Mike's actual receipts, which don't exist in this
repository), consistent with every other lane's walkthrough; nothing
about this gate required or used real production data.

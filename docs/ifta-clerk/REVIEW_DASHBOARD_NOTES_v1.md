# Review Dashboard (Phase 3) — NOTES

Branch: `build/ifta-clerk-review-dashboard`, off `integration`. Approved
against `docs/ifta-clerk/IFTA_CLERK_BLUEPRINT_v1.md` section 7, plus new
direction: the Review Dashboard becomes **the primary user experience of
the IFTA Clerk**, while maintaining Evidence First, Read-only Workspace,
Human Authority, Recommendation Packages Only, and explicitly no
QuickBooks/DocuSign/Filing integration. Design brainstormed and approved
before any code — see the conversation's design section for the full
architecture discussion and clarifying-question record.

## Built

- `src/dispatch/ifta_clerk/` — a new, small Flask app, mounted at
  `/ifta-clerk` under the Shell, alongside `/queue`, `/reports`, `/ifta`.
  - `dashboard.py` — `build_dashboard(read_only_conn, *, quarter,
    fuel_type)`, the pure, Flask-free assembly of all seven panels.
    Takes only a read-only connection; every panel is a plain read over
    `fuel_records`/`mileage_records`/`ifta_worksheets`/`ifta_exceptions`/
    `evidence_records`, or a call to `preview()`/`live_indicators()`
    (both already merged). No writer anywhere in this module.
  - `app.py` — `create_app(config)`, one `GET /` route. Bootstraps the
    database file once at startup (matching Reports' own precedent —
    see "Fresh-install gap found" below), then every request uses only
    a read-only connection.
  - `templates/`, `static/style.css`, `readonly.py` (this module's own
    copy, per the established "don't import another lane's internals"
    convention), `README.md`.
- `src/dispatch/ifta/worksheet.py` — one new function,
  `latest_worksheet_for(conn, *, quarter, fuel_type)`: the read `get()`
  alone couldn't answer ("does a real worksheet already exist for this
  quarter?"), needed to decide between showing a real worksheet's stored
  numbers and `preview()`'s live estimate. Orders by `created_at DESC,
  ifta_worksheet_id DESC` — `created_at` is only second-precision, so the
  ULID (millisecond-precision, lexicographically time-sortable) is the
  real tie-breaker for two worksheets built in the same second.
- `src/dispatch/shell/app.py` + `templates/base.html`/`dashboard.html` +
  `static/style.css` — mounts `/ifta-clerk`, adds a nav link, and a
  prominent `card-primary`-styled card at the top of the dashboard's
  summary cards (distinct styling, listed first) — the "primary
  experience" framing made concrete as the first thing Mike sees.
- Tests: `tests/ifta_clerk/` (23 tests — 15 for `dashboard.py`'s seven
  panels, 8 for `app.py`'s routes/structural protections),
  `tests/lane_c/test_worksheet.py` (+5 for `latest_worksheet_for`),
  `tests/shell/test_app.py` (+4 for the new mount, plus the existing
  "only import create_app" AST check extended to all three mounted
  apps). Full repo suite: 416 passed (was 384 before this branch).
- **Manual smoke test against the real running mounted server**: Shell's
  home page showed the IFTA Clerk card first and prominently; followed
  it to a genuinely fresh `/ifta-clerk/` — clean empty state, no crash;
  fed a real fuel CSV through the real `IntakePipeline`, a real mileage
  entry through `tools/mileage_worksheet.py`, and a real rate — the
  dashboard's `fleet_mpg=24.0`, `total_net_tax=0.00` verified by hand;
  a malformed `?quarter=` returned a clean `400` with the real error
  message, not a crash; a real reefer-flagged fuel record rendered as a
  `critical`-severity Category 2 finding while Category 1 correctly
  stayed empty ("no worksheet built for this quarter yet"); independently
  confirmed via raw `sqlite3`, not the app's own code, that
  `audit_log`/`ifta_exceptions`/`ifta_worksheets`/`queue_items` were
  untouched by any of the roughly ten dashboard page loads performed,
  including the failure case.

## Findings made during design and build, decided explicitly, not assumed

- **Panel 6 (evidence links) does not call `EvidenceSpine.retrieve()`.**
  As originally specced it would have — fine for a one-record detail
  page (how Queue's own detail page already works), but `retrieve()`
  writes a real `audit_log` row every call and, on a hash mismatch, a
  real urgent Queue item. Calling it once per fuel record shown on a
  dashboard would mean every page view writes N audit rows — the exact
  class of dashboard-viewing side effect already ruled out for
  `broken_evidence_linkage` in Category 2 Live Indicators. Raised
  directly; Mike chose the plain-reference-read option. Panel 6 reads
  `document_type`/`archive_path`/`file_hash` straight from
  `evidence_records` instead — real, stored values, no re-verification.
- **The rate table version gap.** `preview()` requires a
  `rate_table_version`; there's no global "current" one, and multiple
  can coexist. `_tax_position()` counts distinct `source_version`s for
  the quarter/fuel_type: exactly one is used automatically; zero shows
  "no rate entered yet"; more than one shows "ambiguous, resolve via a
  real build" — never silently picked. Not raised as a question (a
  direct, conservative extension of `IFTA_CONSTITUTION_v1`'s existing
  no-fabrication rule for `MissingRateError`), but documented here for
  visibility.
- **Fresh-install gap found and fixed at the source.** SQLite's
  `mode=ro` connection fails to even open a database file that doesn't
  exist yet — a more fundamental crash than the "no such table" class
  already handled by `_table_exists()` guards. `create_app()` now
  bootstraps the database file once at startup, matching
  `dispatch.reports.app.create_app()`'s own precedent exactly — a
  startup-only exception to "no write-capable connection ever in scope,"
  never per-request, and it only ever touches the common tables
  `bootstrap()` already owns.
- **Suspect-entries double-counting is correct, not a bug.** A single
  low-confidence fuel purchase legitimately produces two suspect
  entries — one `fuel_records` row and one `expense_records` row — per
  the Dual-Record Fuel Doctrine (`DECISION_LOG.md` #2). Confirmed by
  test, not silently "fixed" by deduplicating away real, separately
  governed records.

## Deliberately Not Built

- No write routes, no forms, no way to build/approve/seal anything from
  this app — every write action is a plain link to the real Queue or
  `/ifta`'s own write routes. Matches Human Authority directly.
- No QuickBooks/DocuSign/Filing integration of any kind — trivially true
  this phase, restated explicitly per direction.
- No caching — every panel re-reads real data fresh on every request,
  same as `preview()`/`live_indicators()` already do.
- Confidence threshold stays the same unvalidated `0.75` placeholder
  `validators.py` already uses (`IFTA_CLERK_BLUEPRINT_v1` sections
  9/12.3) — labeled as such in the UI, not silently presented as
  calibrated.

## Deferred

- `broken_evidence_linkage`'s future path and folding the five
  worksheet-dependent detectors into Category 2 via `preview()` remain
  open questions (`IFTA_CLERK_BLUEPRINT_v1` sections 12.7, 12.8) —
  untouched by this phase.

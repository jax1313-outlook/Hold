# Prepare This Quarter / Submit for Approval — NOTES

Branch: `build/ifta-clerk-prepare-quarter`, off `integration`. Approved
against `docs/ifta-clerk/IFTA_CLERK_BLUEPRINT_v1.md` section 13, Phase 5
— the blueprint's original three-step design ("`build()` +
`run_all_detectors()` + `submit_for_approval()` in sequence") modified
by direction 2026-08-04: submission stays a separate human action,
never bundled into preparation, to maintain a clear separation between
Preparation / Review / Approval Routing.

## Built

- `src/dispatch/ifta_clerk/prepare.py` — the app's first write-capable
  module, kept deliberately separate from `dashboard.py` (which stays
  exactly as read-only as it always was):
  - `prepare_quarter(write_conn, read_only_conn, roots, *, quarter,
    fuel_type)` — calls the real `WorksheetEngine.build()` then the real
    `run_all_detectors()`, in sequence. **Never calls
    `submit_for_approval()`.** Uses the same rate-table-version
    auto-resolution `dashboard.py`'s `preview()` call already uses
    (exactly one distinct `source_version` → use it; zero → refuse;
    more than one → refuse as ambiguous) — shared via a new public
    `distinct_rate_versions_for_quarter()` in `dashboard.py`, not
    reimplemented a second time.
  - `submit_quarter_for_approval(write_conn, *, quarter, fuel_type)` — a
    deliberately separate action, calling only `submit_for_approval()`.
    Refuses cleanly (`NothingToSubmitError`) if nothing's been prepared
    yet, and (`AlreadySubmittedError`) if the worksheet's
    `queue_item_id` is already set — calling it twice never creates a
    second approval Queue item.
  - Neither function ever imports or calls `attempt_seal()` — sealing
    stays exactly where it already was.
- `src/dispatch/ifta_clerk/app.py` — two new routes, `POST /prepare` and
  `POST /submit`, the app's only write-capable endpoints. Both use the
  PRG (POST-redirect-GET) pattern: on success, redirect back to the
  dashboard with a `prepared=1`/`submitted=1` query flag that renders a
  success banner; on failure, render the dashboard template directly
  with a clear error message, never a raw crash. `app.py` itself never
  imports `QueueStore`/`dispatch.ifta.package` directly — it only calls
  `prepare.py`'s two functions.
- `src/dispatch/ifta_clerk/templates/dashboard.html` — a "Prepare This
  Quarter" button when only a live estimate exists (no real worksheet
  yet), and a "Submit for Approval" button when a real, not-yet-submitted
  worksheet exists — mutually exclusive, matching the tax-position
  panel's existing "never both at once" rule.
- Tests: 19 new (11 in `tests/ifta_clerk/test_prepare.py` for the
  business logic, 8 new/updated in `tests/ifta_clerk/test_app.py` for
  the routes and updated boundary guards). Full repo suite: 435 passed
  (was 416 before this branch).
  - The separation itself is proven structurally, not just asserted:
    `prepare_quarter`'s own function source never references
    `submit_for_approval`; `submit_quarter_for_approval`'s own function
    source never references `.build(`/`run_all_detectors`; the whole
    `ifta_clerk` package's `ast`-parsed imports never include
    `attempt_seal`, anywhere.
  - The old `test_ifta_clerk_app_has_no_post_routes` test (accurate
    before this branch) is replaced with
    `test_ifta_clerk_app_has_exactly_two_post_routes`, asserting the
    *only* two POST-capable endpoints are `prepare`/`submit` — not
    silently dropped, corrected to match the new, deliberately narrow
    reality.
- **Manual smoke test against the real running mounted server**: real
  fuel/mileage/rate data through real entry points → `POST /prepare` →
  real 302 redirect → real worksheet (`fleet_mpg=20.0`, correctly
  flagged `fleet_mpg_out_of_band` since 20.0 mpg is outside the
  plausible `[4.0, 9.5]` band — a real detector correctly firing, not a
  bug) → independently confirmed via raw `sqlite3` that `queue_item_id`
  was still `NULL` (no auto-submit) → `POST /submit` → real approval
  Queue item created → confirmed via raw `sqlite3` → a second `POST
  /submit` cleanly refused (400, clear message), confirmed via raw
  `sqlite3` that the approval-queue-item count stayed at exactly 1 →
  the real, completely unmodified `/queue/` app independently showed
  the exact approval item this workflow created ("Approve IFTA
  worksheet 2026-Q3 (diesel): net tax 0.00").

## Findings made during design, decided explicitly

- **"Assemble review package" needed no new artifact.** The already-built
  Review Dashboard assembles exactly this the moment a real worksheet
  exists — `tax_position` switches to the real worksheet,
  `confirmed_exceptions` shows the real persisted findings, automatically,
  via `latest_worksheet_for()`. `prepare_quarter()`'s job ends the
  instant `build()`/`run_all_detectors()` succeed; the dashboard *is*
  the review package.

## Deliberately Not Built

- No form field to pick a `rate_table_version` manually — same
  no-fabrication auto-resolution `preview()` already uses. If ambiguous,
  Prepare refuses with a clear message rather than presenting a picker;
  a manual override remains available only through `build/ifta-ui`
  (still unmerged, its fate still an open blueprint question).
- No scheduler, no automatic quarter-end trigger — still a human clicking
  a button, per blueprint section 12.1's recommendation and this
  session's unbroken "no production infrastructure" boundary.

## Deferred

Phase 6 (Recommendation Packages) remains undesigned, per blueprint
section 13 — "future, named only." Not touched by this branch.

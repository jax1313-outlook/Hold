# Recommended Payment Amount — NOTES

Branch: `build/ifta-clerk-payment-recommendation`, off `integration`.
Approved 2026-08-05 against `docs/ifta-clerk/IFTA_CLERK_BLUEPRINT_v1.md`
section 13, Phase 6 — the first of three named Recommendation Package
types ("a prepared DocuSign package, a drafted accounting notification,
a recommended payment amount — proposals, never live sends"), chosen to
build first because it has zero external-system dependency (no DocuSign
schema, no accounting-system format exists anywhere in this codebase to
design against).

## Design, as approved ("yes proceed")

- Applies only to a real, **sealed** worksheet — matching blueprint
  section 2's "after sealing" placement. A draft worksheet, or no
  worksheet at all, refuses cleanly.
- Computation wraps the sealed worksheet's own already-approved
  `total_net_tax` in a label: `remit` (positive), `credit` (negative,
  reported as a positive amount), or `no_payment_due` (zero). No new
  number is invented or re-derived.
- Persistence is one JSON file to Archive
  (`ARCHIVE\IFTA\<quarter>\<id>_payment_recommendation.json`), the same
  root `attempt_seal()` already writes its own sealed bundle to. No new
  database table or column.
- Boundary: no payment API, no bank integration, no accounting write
  exists anywhere in this codebase for the recommendation to reach.
  Generating it is the entire action.

## Built

- `src/dispatch/ifta_clerk/recommend.py` — the app's third write-capable
  module, kept separate from `dashboard.py` and `prepare.py`:
  - `compute_payment_recommendation(worksheet)` — pure function, no I/O.
    Three branches: `total_net_tax > 0` → `remit`, amount = the value
    itself; `< 0` → `credit`, amount = `abs(total_net_tax)` (always
    reported positive, never a negative payment amount); `== 0` →
    `no_payment_due`, amount `0.0`.
  - `recommendation_path(roots, quarter, ifta_worksheet_id)` /
    `existing_recommendation(roots, quarter, ifta_worksheet_id)` — the
    idempotency check: file existence, not a new schema flag.
  - `generate_payment_recommendation(read_only_conn, roots, *, quarter,
    fuel_type)` — the one real write action. Structurally incapable of
    touching the database at all: its **only** connection parameter is
    `read_only_conn`. Looks up the latest worksheet via
    `dispatch.ifta.worksheet.latest_worksheet_for()`; refuses
    (`WorksheetNotFoundForRecommendationError`) if none exists yet;
    refuses (`WorksheetNotSealedError`) if the latest one isn't sealed;
    returns the existing recommendation unchanged if one was already
    generated (the sealed numbers it's built from can never change, so
    regenerating would be pointless); otherwise computes and writes
    exactly one file.
- `src/dispatch/ifta_clerk/app.py` — `POST /recommend-payment`, the
  app's third and final write-capable endpoint, same PRG pattern as
  `/prepare`/`/submit`: success redirects with `recommended=1`; failure
  renders the dashboard template directly with a clear 400 error, never
  a raw crash. A new `_payment_recommendation_for()` helper computes
  what (if anything) to show on the dashboard route itself, reading via
  `existing_recommendation()` — no write happens just from viewing.
- `src/dispatch/ifta_clerk/templates/dashboard.html` — inside the
  existing sealed-worksheet branch of the tax-position panel: shows the
  generated recommendation (badge "RECOMMENDATION — NOT A PAYMENT", the
  amount and label, a "proposal only" hint) if one exists, otherwise a
  "Generate Payment Recommendation" button — mutually exclusive, same
  rule the panel already follows for draft vs. sealed vs. estimate.
- `src/dispatch/ifta_clerk/static/style.css` — `.badge-recommendation`,
  `.recommendation`.
- Tests: 17 new (13 in `tests/ifta_clerk/test_recommend.py` for the
  business logic, 4 new route tests in `tests/ifta_clerk/test_app.py`
  using a `_seal_a_real_worksheet_via_app()` helper that drives
  `/prepare` + `/submit` through the real app, then approves and seals
  directly via `QueueStore.approve()` / `dispatch.ifta.package
  .attempt_seal()` since neither is reachable through `ifta_clerk`
  routes). Full repo suite: 452 passed (was 435 before this branch).
  - The boundary is proven structurally, not just asserted:
    `generate_payment_recommendation`'s first parameter is literally
    named `read_only_conn`, checked via `inspect.signature`; the whole
    `recommend.py` module's `ast`-parsed imports never include
    `requests`/`smtplib`/`urllib`/`http.client`/`QueueStore`/
    `EvidenceSpine`/`attempt_seal`/`submit_for_approval`, and never
    import `dispatch.ifta.package` at all; no raw `INSERT`/`UPDATE`/
    `DELETE` SQL string appears anywhere in the module;
    `compute_payment_recommendation`'s own source never contains
    `open(`/`write_text`/`Path(` — proof it's pure.
  - `test_ifta_clerk_app_has_exactly_two_post_routes` renamed to
    `test_ifta_clerk_app_has_exactly_three_post_routes`, asserting the
    only three POST-capable endpoints are `prepare`/`submit`/
    `recommend_payment` — not silently dropped, corrected to match the
    new, deliberately narrow reality.
- **Manual smoke test against the real running mounted server**
  (`docs/ifta-clerk/PAYMENT_RECOMMENDATION_WALKTHROUGH_REPORT_v1.md` has
  the full step-by-step record): failure path first (`POST
  /recommend-payment` with no worksheet at all → clean 400, nothing
  written) → real fuel/mileage/rate data through real entry points,
  spanning two jurisdictions (TX fuel purchase, TX+OK mileage, both
  real rates) → `/prepare` → `/submit` → approved and sealed via the
  real `QueueStore`/`attempt_seal()` (`total_net_tax = -1.4000...`, a
  real credit position, with two real detector findings —
  `fleet_mpg_out_of_band` and `miles_no_fuel_gap` — surfacing honestly
  along the way, not suppressed) → `POST /recommend-payment` → real 302
  → independently confirmed via the filesystem that exactly one new
  file was written (`credit`, `amount: 1.4000000000000004`, matching
  the sealed worksheet's `total_net_tax` by hand) → repeated the POST a
  second time and confirmed no second file, same `generated_at`
  (idempotent for real, not just in the test suite) → the real,
  completely unmodified `/queue/` app independently showed the same
  approved item ("Approve IFTA worksheet 2026-Q3 (diesel): net tax
  -1.40").

## Deliberately Not Built

- No form field or override for the recommendation label or amount —
  it is derived, never entered; there is nothing to override.
- No notification, email, or print action when a recommendation is
  generated — generating the file is the entire action, matching the
  approved design's boundary.

## Deferred

The other two named Recommendation Package types — a prepared DocuSign
package, a drafted accounting notification — remain named-only,
undesigned. Both require a real external format/target (DocuSign,
QuickBooks or similar) that doesn't exist anywhere in this codebase and
that Mike hasn't yet specified; building against a guessed schema would
violate the no-fabrication rule this codebase has held to throughout.

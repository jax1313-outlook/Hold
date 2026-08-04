# Category 2 Live Indicators — NOTES

Branch: `build/ifta-live-indicators`, off `integration`. Approved
directly against `docs/ifta-clerk/IFTA_CLERK_BLUEPRINT_v1.md` section 8
(2026-08-04): "Approved in principle. Proceed with Live Indicators. Add
indicator severity classification. Explicitly document that Live
Indicators remain informational only and never create workflow side
effects. Maintain the same structural protections used by Preview Mode:
read only, non-persistent, no queue activity, no approval activity, no
audit activity." No separate launch package document was written — the
same reasoning as Preview Mode: the approval message already specified
the acceptance criteria precisely.

## Built

- `src/dispatch/ifta/live_indicators.py` — one function,
  `live_indicators(read_only_conn, *, quarter, fuel_type)`. Calls four of
  the ten exception detectors directly — `odometer_discontinuity`,
  `active_truck_days_no_mileage`, `late_arrival_closed_quarter`,
  `reefer_in_propulsion` — never through `run_all_detectors()`, so
  nothing is persisted to `ifta_exceptions` and no Queue item is created
  just because someone viewed a live dashboard.
  - **Scope decision, made explicitly rather than assumed:** the
    blueprint's section 8 named 5 worksheet-free detectors as eligible
    for this category and separately said the other 5
    worksheet-dependent detectors could join "if section 6's preview
    mode is later approved and built." Preview mode landed earlier this
    session. Asked directly whether today's build should therefore cover
    all 10 or stay at the original 5 — Mike chose to keep this build at
    the original 5, treating "fold the worksheet-dependent 5 in via
    preview()" as an explicit, separate follow-on rather than
    scope-creep decided mid-build.
  - **`broken_evidence_linkage` excluded from that 5, found and
    confirmed during design, not assumed:** it shares the same
    worksheet-free function signature as the other four, but its body
    calls `EvidenceSpine.retrieve()`, which unconditionally writes a
    real `audit_log` row every call and, on a hash mismatch, a real
    urgent Queue item — a genuine side effect from merely viewing a
    dashboard. Asked directly how to handle it; Mike chose to exclude it
    from this build rather than accept that side effect. It remains
    available today only through a real `build()` +
    `run_all_detectors()`, as a Category 1 (confirmed) exception — named
    as an open item in the module's own docstring, not silently dropped.
  - **Severity classification**, added per Mike's direction, its own
    closed vocabulary (`SEVERITY_BY_EXCEPTION_TYPE`) — deliberately not
    Lane B's Queue `urgent`/`today`/`whenever` priorities, since a live
    indicator never touches the Queue and must never read as if it had:
    - `reefer_in_propulsion` → `critical` — the router already refuses
      to create this in the first place; firing at all means a bug
      elsewhere or a hand-edited row.
    - `late_arrival_closed_quarter` → `warning` — a document dated
      inside an already-sealed, already-filed quarter; a real
      filing-integrity question needing a human decision.
    - `active_truck_days_no_mileage` → `warning` — a real data gap that
      will block an accurate worksheet build for that truck.
    - `odometer_discontinuity` → `notice` — worth a look, but most
      likely to have an innocuous explanation (a replaced or reset
      odometer).
  - A missing `fuel_records`/`mileage_records`/`ifta_worksheets` table
    (a genuinely fresh install, or a quarter with no worksheet ever
    built) reads as no findings, not a crash — the same reasoning
    `preview()` already applies to its own aggregators, applied here at
    this module's own layer via a small `_safe_call()` wrapper, since
    `exceptions.py` itself is out of this change's scope (matching the
    precedent set with `worksheet.py`'s aggregators: fix the bug class
    at the layer being built, without touching the frozen file
    elsewhere).
- `tests/lane_c/test_live_indicators.py` — 14 tests: matches what each
  detector finds when called individually; each of the four surfaces
  with its documented severity from real seeded data (odometer
  discontinuity → `notice`, active-truck-days → `warning`, late arrival
  → `warning`, reefer-in-propulsion → `critical`); clean empty result on
  a genuinely fresh database; every finding's severity checked against
  the closed vocabulary and explicitly checked to never collide with
  Queue's own vocabulary; and one test per structural protection, each
  checked structurally (`inspect.signature`/`ast`-parsed imports/real row
  counts before and after), not just today's return value:
  1. Read only — the function's only parameter is `read_only_conn`.
  2. Non-persistent — `run_all_detectors` never imported;
     `ifta_exceptions` row count unchanged after a call that produced
     real findings.
  3. No queue activity — `QueueStore`/`dispatch.queue.store` never
     imported; `queue_items` row count unchanged.
  4. No approval activity — `dispatch.ifta.package`,
     `submit_for_approval`, `attempt_seal` never imported.
  5. No audit activity — `EvidenceSpine`, `broken_evidence_linkage`,
     `write_audit_entry`, `dispatch.common.audit` never imported;
     `audit_log` row count unchanged after a call that produced real
     findings.
  - Plus one test calling `live_indicators()` five times in a row against
    the same real reefer-flagged fuel record, confirming the same single
    finding comes back every time and `ifta_exceptions`/`queue_items`/
    `audit_log` all stay at zero throughout.
- `src/dispatch/ifta/README.md` — new "Live Indicators" subsection under
  "Exception detectors", explaining the module, the severity
  vocabulary, and explicitly naming why `broken_evidence_linkage` is
  excluded.
- Full repo suite: 384 passed (was 370 before this branch).
- **Manual smoke test against a real sandbox database**: fresh database →
  empty findings, no crash → seeded a real reefer-flagged fuel record and
  a real odometer discontinuity through direct real inserts → both
  findings surfaced with the correct severities (`critical`, `notice`) →
  independently confirmed via raw `sqlite3`, not the project's own code,
  that `ifta_exceptions`/`queue_items`/`audit_log` were all still at zero
  → called `live_indicators()` five more times in a row → all three
  tables still at zero.

## Flagged

- `broken_evidence_linkage`'s exclusion (above) means Category 2 today
  covers 4 of the 10 detectors, not 5 as the blueprint's original text
  named — the blueprint document itself (on the separate, unmerged
  `docs/ifta-clerk-blueprint` branch) has not yet been updated to reflect
  this finding; worth reconciling next time that branch is touched.
- The scope decision to hold at 4/10 rather than fold in the
  worksheet-dependent detectors via `preview()`: real, and intentional,
  not an oversight. `preview()`'s own `InsufficientDataError`/
  `MissingRateError` failure modes would need their own handling inside
  a "live" call before those five could safely join — a real design
  question for that follow-on, not solved here.

## Deliberately Not Built

- No route, template, or UI surface — same reasoning as Preview Mode:
  approved scope was the function only. The full Review Dashboard
  (blueprint phase 3) is a separate, later, its-own-approval piece of
  work.
- No caching — re-reads real data fresh every call, same as `preview()`
  and `build()` already do. Not a concern at current pilot scale.

## Deferred

None — every condition in the approval message was implemented and
independently tested, both automatically and against a real running
database.

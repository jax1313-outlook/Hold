# Mileage Entry / Mileage Source Strategy — NOTES

Branch: `build/mileage-entry-ui`, off `integration`. Resolves
`IFTA_CLERK_BLUEPRINT_v1.md` section 12's open question 2 ("Is manual
entry (already built) acceptable as the ongoing source of truth
indefinitely, or is there a real future plan... that should be scoped
as a later phase?") — the last item of Mike's original 5-item work
list.

## The decision

**Manual entry, permanently.** Not a placeholder pending a future
integration — a standing answer. There is no ELD/GPS/odometer-device
integration anywhere in this codebase, and none is planned. This was
already decided twice before this branch existed: the original
DispatchPilot direction, and blueprint section 3 ("There is no ELD
integration (explicitly out of scope, both in the earlier DispatchPilot
direction and unchanged here)"). An ELD hours-of-service export was
even dropped into Pilot Run 1 and correctly registered as evidence only
— no extraction logic exists or is planned for it. Confirmed directly
("yes, go ahead and build it") against a presented design.

## What was actually still open, and what this branch closes

Two real, concrete gaps — not the source-of-truth question itself,
which was already settled, but two operational consequences of leaving
it unaddressed:

1. **Mileage entry was the one CLI-only write action** in an otherwise
   browser-driven IFTA workflow — flagged directly in
   `docs/pilot/DISPATCH_PILOT_RUN_2_REPORT_v1.md`'s findings ("someone
   still has to run `tools/mileage_worksheet.py`... by hand").
2. **Manual mileage has no independent cross-check** — both Run 1 and
   Run 2 independently produced a borderline/implausible fleet MPG from
   manually-entered mileage, caught only by `fleet_mpg_out_of_band`,
   and only after a full worksheet build (downstream, not at entry).

## Built

- `src/dispatch/ifta/mileage.py` (new) — `record_mileage()` moved here
  from `tools/mileage_worksheet.py`, so the CLI tool and the new UI
  route share one real write path instead of two copies of the same
  `INSERT`. Takes an already-open connection (matching
  `attempt_seal()`/`prepare_quarter()`'s shape) rather than a config
  dict that bootstraps its own — the caller owns connection lifecycle,
  consistent with every other write action in this app.
- `tools/mileage_worksheet.py` — now a thin argparse wrapper around
  `dispatch.ifta.mileage.record_mileage()`, unchanged in behavior
  (`tests/lane_c/test_mileage_worksheet_tool.py` proves the re-export
  still resolves to a working function).
- `src/dispatch/ifta/worksheet.py` — `live_fleet_mpg_estimate(read_only_conn,
  *, quarter, fuel_type) -> float | None`, new public function. Reuses
  the exact same `_aggregate_mileage`/`_aggregate_fuel` `build()` and
  `preview()` already share — deliberately independent of any rate
  table, unlike `preview()`, since fleet_mpg never involves a rate.
  Returns `None` on insufficient data rather than raising or guessing.
- `src/dispatch/ifta_clerk/app.py` — `POST /record-mileage`, the app's
  fourth and (for now) final write-capable route. Validates required
  fields (clean 400 + typed message on any missing field, matching
  every other write route's error handling — never a raw crash), then
  writes via `record_mileage(get_write_conn(), ...)`, then computes
  `live_fleet_mpg_estimate()` for the request's quarter/fuel_type: if
  it falls outside `exceptions.DEFAULT_MPG_BAND` (`(4.0, 9.5)` — the
  same constant the detector uses, not a second competing threshold),
  the redirect carries an `mpg_warning` query value the dashboard
  renders as a non-blocking banner. **The entry is never refused** for
  implausibility — mileage is Mike's own attestation, and this route
  doesn't get to reject it, only flag it earlier than the detector
  would.
- `src/dispatch/ifta_clerk/templates/dashboard.html` — a collapsible
  "Record mileage" form (unit, jurisdiction, period, miles, entered by)
  next to the Miles by Jurisdiction panel, available regardless of
  worksheet state; a `mileage_recorded` success banner; the plausibility
  warning banner when present.
- `src/dispatch/ifta_clerk/static/style.css` — `.banner-warning`,
  `.mileage-entry`, `.mileage-form`.
- Tests: 10 new (3 in `tests/lane_c/test_worksheet.py` for
  `live_fleet_mpg_estimate` — matches a real build with no rate needed,
  `None` with no data, `None` with mileage but no fuel; 2 in
  `tests/lane_c/test_mileage.py` for the moved `record_mileage()`; 5 new
  route tests in `tests/ifta_clerk/test_app.py` — real write + redirect,
  missing-fields refusal, non-numeric miles refusal, warning fires and
  the entry still succeeds, no warning when plausible).
  `tests/lane_c/test_mileage_worksheet_tool.py` collapsed from two full
  duplicate tests to one re-export check, since full coverage now lives
  in `test_mileage.py` against the real module directly.
  `test_ifta_clerk_app_has_exactly_three_post_routes` →
  `..._four_post_routes`, asserting the only four POST-capable
  endpoints are `prepare`/`submit`/`recommend_payment`/
  `record_mileage_route`. Full suite: 469 passed (was 460).
- **Manual smoke test against the real running mounted server**: the
  failure path first (all fields missing → clean 400, exact message
  listing every missing field) → a real fuel CSV through the real
  intake pipeline → a real mileage entry through the real form
  (1500mi/100gal = 15.0 mpg) → real 302 with `mpg_warning=15.00` →
  independently confirmed via raw `sqlite3` that the row was written
  anyway, never refused → the dashboard rendered both the success
  banner and the warning banner with the exact value → a second entry
  in a fresh quarter with plausible mileage (700mi/100gal = 7.0 mpg)
  produced no `mpg_warning` at all, confirmed silent.

## Deliberately Not Built

- No blocking validation of any kind on the mileage figure itself —
  the plausibility check is advisory only, matching Human Authority:
  the system doesn't get to reject a human's own attestation, only
  flag it early.
- No ELD/GPS/odometer-device integration, no import format for any of
  them, no field reserved for a future one beyond the `odometer_start`/
  `odometer_end` columns the schema already had (optional context, not
  a second source of truth).
- No per-unit mileage view or unit-level plausibility check — the
  estimate is fleet-wide, matching `fleet_mpg_out_of_band`'s own scope
  exactly (computation spec 3.5 has always been fleet-wide, not
  per-unit).

## Deferred

None — this was the last item of Mike's original 5-item work list.

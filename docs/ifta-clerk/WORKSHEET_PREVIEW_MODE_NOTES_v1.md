# WorksheetEngine Preview Mode — NOTES

Branch: `build/ifta-worksheet-preview`, off `integration`. Approved
directly against `docs/ifta-clerk/IFTA_CLERK_BLUEPRINT_v1.md` section 6.1
(2026-08-04), under six explicit conditions given by Mike — that approval
served the role a launch package normally would; no separate launch
package document was written since the six conditions already specified
the acceptance criteria precisely.

## Built

- `src/dispatch/ifta/worksheet.py` — a new module-level `preview()`
  function: a live, non-persisting estimate of what `WorksheetEngine.build()`
  would produce right now, computed from real current data, never written
  anywhere.
  - Takes exactly one parameter, `read_only_conn` — no write-capable
    connection is ever in scope inside it. This is the same genuine
    SQLite `mode=ro` connection `WorksheetEngine` already uses for
    source-immutability; any write attempted through it, against any
    table, raises immediately.
  - To share computation spec 3.5 in exactly one place rather than
    reimplementing it, three pieces of `WorksheetEngine.build()`'s
    previously-inline/instance-method logic became module-level
    functions both `build()` and `preview()` call: `_aggregate_mileage`,
    `_aggregate_fuel` (now take `conn` as a parameter instead of reading
    `self._ro_conn`), and a new `_compute_worksheet_lines` (the
    fleet_mpg/taxable_gallons/net_tax arithmetic itself, extracted out of
    `build()`'s body unchanged). `build()` and `preview()` are now two
    thin callers of the same three functions — one persists afterward,
    one doesn't.
  - Side effect of that refactor, done deliberately as part of it (not a
    drive-by fix elsewhere): `_aggregate_mileage`/`_aggregate_fuel` now
    check table existence first and return empty results instead of
    letting a genuinely fresh database's missing `fuel_records`/
    `mileage_records` table raise a raw `sqlite3.OperationalError`. This
    is the exact bug class `docs/ifta-ui/NOTES.md` (on the unmerged,
    superseded `build/ifta-ui` branch) already documented as needing a
    "future dedicated fix in `worksheet.py` itself" — fixing it here, in
    the same functions being touched for Preview Mode, is that dedicated
    fix, not a new drive-by patch of unrelated code. `build()` inherits
    the fix as a consequence of sharing the same functions.
  - `preview()` needed one more guard beyond that: `rates.get_rate()`
    calls `install_schema()` internally (a `CREATE TABLE IF NOT EXISTS`),
    which is a genuine no-op against an existing table even through a
    read-only connection (verified directly against real SQLite
    behavior, not assumed) but raises if the table doesn't exist yet at
    all. `preview()` checks `rate_tables` exists before doing anything
    else and raises a clean `InsufficientDataError` ("no rate has ever
    been entered against this database") rather than surfacing that raw
    error.
- `tests/lane_c/test_worksheet_preview.py` — 12 new tests: `preview()`
  produces the same numbers `build()` would from identical seeded data;
  raises the same `InsufficientDataError`/`MissingRateError` `build()`
  would for the same bad inputs; behaves cleanly (not a crash) on a
  genuinely fresh database with no schema installed at all; and one test
  per approved condition, each checking the guarantee structurally —
  `inspect.signature`/`__code__.co_names`/`ast`-parsed imports, not just
  today's return value — rather than only checking today's behavior:
  1. No database writes — `preview()`'s only parameter is
     `read_only_conn`, no `self._conn`/`write_conn` anywhere in its body.
  2. No worksheet IDs — `"new_ulid"` never appears in `preview.__code__.co_names`.
  3. No audit status changes — real row counts in `ifta_worksheets`/
     `ifta_worksheet_lines` unchanged before/after calling `preview()`
     against the real database, not just absent from the return value.
  4. No approval path activation — `ast`-parsed imports of
     `dispatch.ifta.worksheet` contain no `QueueStore`, no
     `dispatch.ifta.package`.
  5. Clearly labeled PREVIEW — `result["status"] == "preview"`,
     `result["is_preview"] is True`.
  6. Cannot be mistaken for a filed worksheet — none of
     `ifta_worksheet_id`/`created_at`/`sealed_at`/`queue_item_id` appear
     in a preview result, all four appear in a real `build()`+`get()`
     result, and `status` values differ (`"preview"` vs `"draft"`).
- `tests/lane_c/test_ifta_source_immutability.py` — updated one existing
  test. It previously asserted the literal substring
  `"self._ro_conn.execute"` appeared in `worksheet.py`; after the
  refactor that string no longer exists (the execute calls moved into
  the module-level aggregator functions, generic over whichever
  connection they're handed). Rewritten to check every call site of
  `_aggregate_mileage`/`_aggregate_fuel` in the file passes either
  `self._ro_conn` or `read_only_conn` — stronger than the original
  (checks all call sites, not one example substring), same underlying
  guarantee.
- Full repo suite: 370 passed (was 358 before this branch).
- **Manual smoke test against a real sandbox database** (not just the
  pytest client): a genuinely fresh database → `preview()` raised a
  clean `InsufficientDataError`, not a crash → seeded one real fuel
  purchase, one real mileage record, one real rate → `preview()`
  returned correct numbers (`fleet_mpg=12.0`, TX line with correct
  `taxable_gallons`/`net_tax`) → confirmed **zero** rows in
  `ifta_worksheets` afterward, queried directly against the real
  database, not inferred from the return value → ran a real `build()`
  against the same data for comparison, confirmed identical numbers,
  confirmed exactly one row now exists → ran `preview()` again and
  confirmed the row count stayed at exactly one (a second preview never
  creates a second row, and never collides with the one real worksheet
  that does exist).

## Flagged

- The fresh-database crash fix (bullet above, "side effect of that
  refactor") touches `_aggregate_mileage`/`_aggregate_fuel`, which
  `build()` also uses — so `build()`'s behavior on a fresh database
  changed too: it now proceeds to (correctly) raise
  `InsufficientDataError` from `_compute_worksheet_lines` instead of a
  raw `sqlite3.OperationalError` from a missing table. This is a bugfix,
  not a behavior change any caller could have depended on (the old
  behavior was an unhandled crash), but it's real production code
  outside the new `preview()` surface and is called out explicitly here
  rather than folded in silently.
- `build/ifta-ui`'s own `app.py` still carries its UI-layer workaround
  for the same bug (catching `sqlite3.OperationalError` around calling
  `build()`). That branch is unmerged and its fate is still open
  (`IFTA_CLERK_BLUEPRINT_v1.md` section 12, open question 4) — this
  branch does not touch it. If/when that branch is revisited, its
  workaround is now redundant but harmless; worth removing then, not
  now, since touching an unmerged branch's code isn't part of this
  approved task.

## Deliberately Not Built

- No route, template, or UI surface for `preview()` — approved scope was
  the engine function only. `IFTA_CLERK_BLUEPRINT_v1.md` phase 4 names
  this as the deliverable; phases 2/3/5 (Category 2 Live Indicators, the
  full Review Dashboard, the Clerk's own trigger) are separate, later
  phases, each requiring their own approval.
- No caching or rate-limiting of `preview()` calls — it re-reads
  `fuel_records`/`mileage_records`/`rate_tables` fresh every call, same
  as `build()` already does. Not a concern at current pilot scale; not
  solved preemptively.

## Deferred

None — every one of the six approved conditions was implemented and
independently tested, both automatically and against a real running
database.

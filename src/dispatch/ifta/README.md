# dispatch.ifta — worksheet engine, exceptions, package builder

Implements the IFTA Agent's boundary clause (`IFTA_CONSTITUTION_v1`):
"prepares worksheets, exceptions, and packages from supplied fuel and
mileage records; never adjusts source data, never corresponds with a tax
authority, never files or pays."

## The worksheet engine (`worksheet.py`)

```python
from dispatch.common.db import bootstrap
from dispatch.ifta.readonly import open_read_only
from dispatch.ifta.worksheet import WorksheetEngine

write_conn = bootstrap(config["database"])
read_only_conn = open_read_only(config["database"])
engine = WorksheetEngine(write_conn, read_only_conn)

worksheet = engine.build(quarter="2026-Q2", fuel_type="diesel", rate_table_version="fixture-v1")
```

Computation spec 3.5, verbatim: `fleet_mpg = total_miles_all_jurisdictions
/ total_tractor_gallons_normalized`; per jurisdiction J, `taxable_gallons_J
= miles_J / fleet_mpg` and `net_tax_J = taxable_gallons_J × rate_J −
tax_paid_gallons_J × rate_J` (plus a surcharge line when the rate table
carries one). Rates come only from the versioned `rate_tables` for the
requested `(jurisdiction, quarter, fuel_type, source_version)` — a
jurisdiction with activity but no matching rate raises `MissingRateError`
rather than defaulting to anything. The worksheet is created `draft` and
records exactly which `rate_table_version` it used.

### Preview Mode — a live estimate, never persisted

```python
from dispatch.ifta.worksheet import preview

read_only_conn = open_read_only(config["database"])
estimate = preview(read_only_conn, quarter="2026-Q2", fuel_type="diesel", rate_table_version="fixture-v1")
```

`preview()` runs the same computation spec 3.5 arithmetic `build()` does,
against real current data, and returns it — but never writes anything.
It's a module-level function, not a method, and takes only a read-only
connection: there is no write-capable connection anywhere in its scope to
write with. The returned dict carries `"status": "preview"` and
`"is_preview": True`, and has no `ifta_worksheet_id`, `created_at`,
`sealed_at`, or `queue_item_id` — nothing a caller could mistake for a
real, filed worksheet or feed into `submit_for_approval()`/`attempt_seal()`.
Calling it never creates a queue item and never changes anything in
`ifta_worksheets`/`ifta_worksheet_lines`, no matter how many times it's
called. See `docs/ifta-clerk/WORKSHEET_PREVIEW_MODE_NOTES_v1.md` for the
full approval history and test coverage.

## Source-immutability

"The IFTA Agent cannot alter a fuel or mileage record to balance a
worksheet — enforced via read-only views, verified with a negative test."
`WorksheetEngine` takes **two** connections: `write_conn` for the
`ifta_*` tables it owns, and `read_only_conn` — a genuine SQLite
`mode=ro` connection to the same database file (`readonly.py`) — for
every read of `fuel_records`/`mileage_records`. Any write attempted
through that second connection, against *any* table, raises
`sqlite3.OperationalError` immediately. That's a real enforcement
mechanism, not a convention the code happens to follow.

## Exception detectors (`exceptions.py`)

All ten from `IFTA_CONSTITUTION_v1`'s exception list: `fuel_no_miles`,
`miles_no_fuel_gap`, `fleet_mpg_out_of_band`, `odometer_discontinuity`,
`active_truck_days_no_mileage`, `broken_evidence_linkage`,
`late_arrival_closed_quarter`, `rate_version_mismatch`,
`reefer_in_propulsion`, `corner_clipping`. Each is a pure function
returning plain finding dicts; `run_all_detectors()` persists every
finding to `ifta_exceptions` and raises one `queue_item` per finding. The
IFTA Agent never auto-resolves any of them — that's the whole point of
routing every one through the Manager's queue.

`reefer_in_propulsion` is a pure safety net: the router refuses outright
to create a reefer-flagged `FuelRecord` in the first place
(`router.ReeferMisroutedError`). This detector exists for the one way it
could still happen — a bug elsewhere, or a hand-edited row — and should
always come back empty in correct operation.

### Live Indicators (`live_indicators.py`) — informational only

```python
from dispatch.ifta.live_indicators import live_indicators

read_only_conn = open_read_only(config["database"])
result = live_indicators(read_only_conn, quarter="2026-Q2", fuel_type="diesel")
```

Four of the ten detectors — `odometer_discontinuity`,
`active_truck_days_no_mileage`, `late_arrival_closed_quarter`,
`reefer_in_propulsion` — take only a read-only connection and a date
range or fuel type, never a built worksheet. `live_indicators()` calls
them directly, **never through `run_all_detectors()`**, so nothing is
persisted to `ifta_exceptions` and no Queue item is ever created just
because someone viewed a live dashboard. Each finding carries a
`severity` (`critical`/`warning`/`notice`) from `SEVERITY_BY_EXCEPTION_TYPE`
— its own vocabulary, deliberately distinct from the Queue's
`urgent`/`today`/`whenever` priorities, since a live indicator never
touches the Queue.

`broken_evidence_linkage` is the fifth worksheet-free detector by
signature alone, and is deliberately **not** included here: it calls
`EvidenceSpine.retrieve()`, which always writes a real `audit_log` row
and, on a hash mismatch, a real urgent Queue item — a side effect from
merely viewing a dashboard, exactly what this module exists to avoid. It
remains available today only through a real `build()` +
`run_all_detectors()`, as a Category 1 (confirmed) exception. See
`docs/ifta-clerk/IFTA_CLERK_BLUEPRINT_v1.md` section 8 for the full
Category 1 / Category 2 distinction, and
`docs/ifta-clerk/LIVE_INDICATORS_NOTES_v1.md` for this module's approval
history and test coverage.

## Package builder (`package.py`)

```python
from dispatch.ifta.package import submit_for_approval, attempt_seal

queue_item = submit_for_approval(conn, queue_store, worksheet)
# ... a human approves queue_item through Lane B's queue ...
sealed = attempt_seal(conn, queue_store, config["roots"], worksheet["ifta_worksheet_id"])
```

`submit_for_approval` creates the `approval` queue item and links it to
the worksheet. `attempt_seal` checks that link: if the queue item isn't
`approved` yet, it raises `ApprovalNotYetGrantedError` rather than doing
anything — there is no other way for a worksheet to reach `sealed`. On
approval, it writes the full bundle (worksheet + lines + who approved it)
to `ARCHIVE\IFTA\<quarter>\<worksheet_id>.json` and flips the worksheet's
status. Like every other lane, there is no background process polling
for approvals — a human or a scheduled task calls `attempt_seal`
explicitly, after the fact.

## Fixture rate data

`rates.py`'s fixture rows exist for this lane's own testing only, tagged
with a `source_version` like `"fixture-v1"` that could never be mistaken
for a real quarterly publication citation. They are never installed via
`tools/seed_library.py` — see `library_seed/RateTables/README.md` for the
real-data gap this doesn't resolve.

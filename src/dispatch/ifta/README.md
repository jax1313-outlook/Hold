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

## The web UI (`app.py`)

Per `docs/ifta-ui/DISPATCH_IFTA_UI_LAUNCH_PACKAGE_v1.md`: closes the gap
two real pilot runs found
(`docs/pilot/DISPATCH_PILOT_RUN_2_REPORT_v1.md` finding #2) — mileage
entry, worksheet building, and sealing all required Python/CLI before
this. Mounted at `/ifta` under `dispatch.shell`. Approval stays exactly
where it already works: the mounted Queue at `/queue`.

Every write route calls one of the functions documented above,
unmodified — `rates.insert_rate()`, `WorksheetEngine.build()`,
`run_all_detectors()`, `submit_for_approval()`, `attempt_seal()` (whose
real refusal-before-approval is preserved exactly, only surfaced). The
one exception is mileage entry, which duplicates (doesn't import)
`tools/mileage_worksheet.py`'s `record_mileage()` INSERT, since that
script lives outside `src/dispatch` and isn't meant to be imported as a
library — both stay independently correct against the same real
`mileage_record.schema.json` shape.

`POST /build` calls `WorksheetEngine.build()` and `run_all_detectors()`
together, in one request — two separate functions in the existing code,
called as one action here, so Mike always sees a worksheet's exception
findings alongside its numbers before deciding whether to submit it.
`MissingRateError`/`InsufficientDataError` render as a clear message on
the form, never a raw 500.

`create_app()` eagerly calls `dispatch.ifta.db.install_schema()` at
startup, the same fix Reports' own app.py already applies to
`print_queue` — `rate_tables`/`ifta_worksheets`/etc. are otherwise
created lazily the first time something real happens, so a genuinely
fresh install would 500 on its very first page load without this.

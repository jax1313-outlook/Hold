# dispatch.reports — the deterministic answer surface

Implements `REPORTS_CHARTER_v1.md`'s two bright lines: read-only except
one narrow writer, and arithmetic yes, domain judgment never. This is a
layer, not an agent — for the person using it, this screen is Dispatch.

## The read-only / single-writer split

- `readonly.py` opens a genuine SQLite `mode=ro` connection — every query
  in `queries.py` runs through it. Any write attempt on that connection,
  against *any* table, raises `sqlite3.OperationalError` immediately.
- `snapshot.py`'s `ReportSnapshotWriter` is the **only** thing in this
  package that opens a normal read-write connection, and it only ever
  writes to `print_queue` and `ARCHIVE\ReportSnapshots\`.

This is deliberately duplicated from Lane C's `dispatch.ifta.readonly`
rather than imported — see the launch package §4: Reports never imports
business logic from `evidence`/`queue`/`receipt`/`ifta`, only
`dispatch.common` (the audit writer, `bootstrap`, `ids`). Everything else
it needs from those lanes' tables, it reads directly via SQL.

## Templates are data

A report is a versioned JSON file under `LIBRARY\Templates\Reports\`
(`templates_engine.py` loads it): which field is the big number, which
breakdown table to show, how each column is formatted. `rendering.py`
turns `(template, data, as_of, period_label, filters)` into HTML — the
exact same function serves the live page and the immutable snapshot, so
"identical inputs produce identical bytes" is one code path, not two that
could quietly drift apart.

Adding a fourth report type is a template file (`library_seed/Templates/Reports/<name>.v1.json`)
plus a fixture — `templates_engine.py` and `rendering.py` never change
for it. The one thing that *is* code, not data: the actual aggregation
query for that report type, added to `queries.py`. The "zero code
change" promise is about the rendering/layout engine, not about
inventing a new SQL aggregation from nothing.

## The three report types

- **Fuel Spend** (`fuel_records`) — total $ and gallons for the period,
  broken down by jurisdiction.
- **Expense Summary** (`expense_records`) — total by category (the
  frozen closed vocabulary); when a Category filter narrows to one,
  shows the line items behind it instead of a one-row breakdown of
  itself.
- **IFTA Position** (`ifta_worksheets` / `ifta_worksheet_lines`) — reads
  `fleet_mpg` and `net_tax` exactly as stored, labeled "Prepared —
  estimate, not filed," exception count inline. No arithmetic happens on
  these values beyond formatting for display — recomputing them here is
  exactly the "divergent numbers" failure mode the charter calls out by
  name. IFTA is inherently quarterly, so it derives its quarter from the
  selected Date Range's end date rather than taking one of its own; it
  also doesn't apply the Truck/State filters in v1, since filtering the
  per-jurisdiction breakdown without also changing the stored
  quarter-level total would make the big number and the table visibly
  disagree — flagged in `docs/lanes/D/NOTES.md`, not silently done.

## Save For Printing

`ReportSnapshotWriter.save_snapshot()` renders a full, self-contained
HTML document (inline CSS, no external asset references — it has to
still make sense as a standalone archived file) and writes it to
`ARCHIVE\ReportSnapshots\<year>\<id>.html`, then inserts one `print_queue`
row referencing it. The queue never holds a second copy of the data.

`print_queue` never gets a `DELETE` code path. "Clearing" an entry is a
status transition (`queued` → `printed` → `cleared`), the same shape
Lane B gave `queue_items` — see `db.py`'s docstring for why this
sidesteps rather than resolves the tension with "no worker deletes
anything, ever."

`create_app()` installs `print_queue`'s schema once at startup, via a
throwaway bootstrap connection. It has to: that table otherwise only
gets created the first time `ReportSnapshotWriter` runs, and the
homepage calls `recent_reports()` on the read-only connection before
anyone has necessarily saved anything — caught by running the real dev
server against a brand-new database, the same way Lane B's threading bug
was, not by the automated suite.

## Recents

The chips on the home page are the last three *saved* report
configurations (from `print_queue`), not a log of every live view. The
charter's bright line is "writes nothing except the print queue" —
tracking every ephemeral view would need a second write path, which
would violate that line for a convenience feature. `snapshot.recent_reports()`
derives recents from data that's already being written for an
unrelated, required reason.

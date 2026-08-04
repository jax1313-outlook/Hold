# dispatch.evidence — the archive/evidence interface

Implements contract 1.4 (`contracts/evidence_record.schema.json`'s
`interface_note`) exactly: three operations, no update, no delete,
permanently.

## Construction

```python
from dispatch.common.db import bootstrap
from dispatch.evidence.interface import EvidenceSpine

conn = bootstrap(config["database"])
spine = EvidenceSpine(conn, config["roots"])
```

`roots` is the config's `roots` dict (`operations` / `library` / `archive`
paths). Nothing in this module hardcodes a filesystem root — per
`DISPATCH_BASE_CONSTITUTION_v1` #1, every path comes from
`dispatch.config.json`, threaded in by the caller. A bare module-level
function couldn't get a connection or roots from anywhere without either
hidden global state or a hardcoded root, so the interface is a small class
instead: one instance per process, constructed once at startup.

## `register(file_path, document_type, metadata) -> EvidenceRecord`

1. Hashes the source file (SHA-256).
2. If a record with that `file_hash` already exists, no new file is copied
   and no new row is inserted — the existing record is returned with
   `extraction_status` overridden to `duplicate_document` **in the returned
   dict only**. The stored row is never touched (no update code path exists
   on `evidence_records`, including for this case) — the flag exists purely
   to tell the caller "you already have this document," not to mark the
   canonical record as anything other than what it always was.
3. Otherwise: copies the original into
   `<archive_root>/Evidence/<YYYY>/<MM>/<evidence_record_id><ext>`
   (`YYYY`/`MM` from `capture_date`, defaulting to the moment of
   registration), re-hashes the copy and refuses to proceed if it doesn't
   match the source hash, sets the copy read-only, verifies the read-only
   attribute actually took effect (checks the mode bits directly — doesn't
   just call `chmod` and assume, since a process with override privileges
   can still write through a read-only bit and would otherwise mask a
   failed `chmod`), inserts the `EvidenceRecord`, writes the Library index
   entry, and returns the full record.
4. `document_date` is required in `metadata` and is never fabricated if
   missing — `register()` raises `ValueError` instead of guessing one.
5. Writes one audit entry: `outcome="completed"` for a fresh registration,
   `outcome="flagged"` for a duplicate hit.

**`archive_path` storage format.** The schema's field description shows
`ARCHIVE\Evidence\YYYY\MM\<evidence_id>.<ext>` — that's the tier name and
Windows separator style the production target (`D:\Archive\...`) will
actually use. What's stored in the `archive_path` column is the part
*relative to the configured archive root*, forward-slash-normalized
(`Evidence/2026/08/<id>.pdf`), not that literal string. Reconstructing the
absolute path is `Path(roots["archive"]) / record["archive_path"]`, which
`pathlib` resolves correctly on both POSIX and Windows (Windows accepts
forward slashes fine). This is the risk #1 mitigation from the launch
package: build and store paths in an OS-agnostic form rather than
hardcoding backslashes, so sandbox tests on Linux/Mac prove the same path
logic that runs on the Windows production target.

## `retrieve(evidence_record_id) -> (EvidenceRecord, absolute_path)`

Re-hashes the file at `archive_path` and compares it to the stored
`file_hash`. On a match, writes a `completed` audit entry and returns the
record plus the resolved absolute `Path`. On a mismatch (or a missing
file), it:

- inserts an `exception` `queue_item` (`contracts/queue_item.schema.json`)
  referencing the evidence record, so the Manager's queue has something to
  show even though Lane B doesn't exist yet — Lane A only needs to know
  the shape, not own the queue;
- writes a `quarantined` audit entry;
- raises `EvidenceIntegrityError`.

This is the Failure Doctrine (`DISPATCH_BASE_CONSTITUTION_v1` #5) applied
literally: stop, quarantine (queue it, don't fix it up), never silently
retry-past a failing item.

## `link_children(evidence_record_id, derived_record_ids) -> EvidenceRecord`

Appends to the container's child list and returns the updated record. The
schema shows `derived_record_ids` as a JSON array column on
`evidence_records`, but growing that array by mutating the column would be
an `UPDATE` against a table with no update code path, permanently. Instead,
children live in a separate append-only table, `evidence_children`
(`evidence_record_id, derived_record_id, linked_at`), with its own
delete/update-revoking triggers. `link_children` only ever `INSERT OR
IGNORE`s into it; `derived_record_ids` on a returned record is always
computed by reading that table back. The result is indistinguishable from
the contract's shape from the outside, while the module surface genuinely
contains zero `UPDATE`/`DELETE` SQL statements against `evidence_records`
— verifiable by grep, not just by reading the code carefully.

## Immutability, end to end

- No method in this class issues `UPDATE` or `DELETE` against
  `evidence_records`, `evidence_children`, or `audit_log`.
- `dispatch.common.db.bootstrap()` installs `BEFORE UPDATE` / `BEFORE
  DELETE` triggers on those same three tables that `RAISE(ABORT, ...)`
  unconditionally — a second, independent enforcement layer in the
  database itself, not just an absence of application code.
- The archived file's read-only bit is a tripwire, not the fence: the code
  path is the actual immutability guarantee (per
  `DISPATCH_BUILD_BLUEPRINT_v1` Part 3.4).

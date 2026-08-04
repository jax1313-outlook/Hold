# dispatch.receipt — intake, extraction, validation, routing

Implements the Receipt Agent's half of the chain (`RECEIPT_CONSTITUTION_v1`):
"a receipt is a container of business transactions." One document may
emit several `FuelRecord`/`ExpenseRecord` rows, all linked back to one
`EvidenceRecord`.

## Pipeline

```python
from dispatch.receipt.intake import IntakePipeline

pipeline = IntakePipeline(config, vendor_profiles=[my_vendor_profile])
summary = pipeline.process_drop()
```

`process_drop()` scans `OPERATIONS\Intake\Drop` **once per call** — there
is no persistent watcher/daemon in this codebase (no other lane runs a
background process either). Call it from a cron job, a manual trigger, or
a scheduled task; it's idempotent, since every file it touches is moved
out of `Drop` before the call returns.

For each file:

1. **Register first, always.** `dispatch.evidence.interface.EvidenceSpine.register()`
   runs before any extraction, per contract 1.4. If registration itself
   fails, the file moves straight to `Intake\Quarantine` and an
   `exception` queue item is created — no evidence record exists yet in
   that case, so the queue item has no `payload_refs`.
2. **Classify and extract.** `.csv` files match against configured vendor
   profiles by an exact filename-prefix match (data, not inference); an
   unmatched `.csv` uses Lane C's own deterministic normalized format
   (`parsers/csv_parser.py`); anything else is treated as a scan and goes
   to the vision extractor. A parse/extraction failure quarantines the
   whole file (it's already registered, so the queue item does reference
   its `evidence_record_id`).
3. **Validate.** Every extracted line — deterministic or vision — passes
   through `validators.validate_document()`: structural check, sum
   validation (whole-document quarantine on mismatch), confidence
   threshold, and transaction-level dedup (each line-level).
4. **Route.** Everything that passed validation goes to `router.py`,
   which creates real `FuelRecord`/`ExpenseRecord` rows per the routing
   table. A routing failure (unclassifiable category, missing unit
   number, a reefer line miscategorized as plain `fuel`) quarantines just
   that line — the rest of the document's lines still route.

## The `document_date` ordering problem

Contract 1.4 requires archiving before extraction; the evidence contract
requires a real, non-fabricated `document_date` at registration time. For
a freshly dropped file, the actual document date (what's printed on it)
is only knowable *after* extraction — which can't run yet, because
registration has to happen first. This module resolves the tension by
registering with the file's own filesystem mtime as `document_date` — a
real fact about the file, honestly labeled, just not necessarily the same
date as what's printed on the document. The *trustworthy* business date
is the `purchase_date` on the resulting `FuelRecord`/`ExpenseRecord`,
extracted properly once extraction actually runs. This is flagged, not
hidden — see `docs/lanes/C/NOTES.md`.

## Vendor profiles

A vendor profile is data: `{"filename_prefix": ..., "column_map": {...},
"total_row_marker_column": ..., "total_row_marker_value": ...}`. Adding a
new fuel-card vendor is a new profile passed into `IntakePipeline`, never
a new code branch that infers a format from content.

## The vision extractor

`extraction/vision.py`'s `ClaudeVisionExtractor` is a real implementation
against the Anthropic API, but nothing in this lane's own test suite ever
calls it live — there are no real credentials in this build environment.
"No API key configured" and "the live call failed" both raise the same
`VisionExtractionUnavailable`, which this pipeline treats as "quarantine
the file" — the exact behavior the stack rationale specifies for a
genuine offline/outage condition. One code path, two occasions to use it.

## Immutability

`fuel_records` and `expense_records` are INSERT-only in this lane's code
— no update path exists for `review_status` or anything else. `db.py`
installs its own delete/update-revoking triggers (this lane can't touch
`src/dispatch/common/db.py`, same reasoning Lane B applied to
`queue_items`).

## Category vocabulary

`vocabulary.py` reads the closed list from
`contracts/expense_vocabulary.schema.json` exactly once; nothing in this
package spells the list out a second time. An unclassifiable category
raises `router.UnclassifiableCategoryError`, caught by the intake pipeline
and turned into a line-level quarantine — never silently accepted, never
extended.

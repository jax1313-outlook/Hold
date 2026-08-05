# Lane C — Receipt → IFTA Chain — NOTES

Branch: `build/receipt-ifta`. Packet: `docs/lanes/C/LANE_C_LAUNCH_PACKAGE_v1.md`.
Merges after Lane A and Lane B (already true structurally: this branch's
history contains both merges).

Update this file at the end of every Lane C session. Do not delete prior
entries — append.

## Session 1 (2026-08-04)

### Built

- **`src/dispatch/receipt/`**: `vocabulary.py` (one source of truth for
  the closed category list), `db.py` (`fuel_records`/`expense_records`
  tables + immutability triggers — this lane's own bootstrap, since
  `common/db.py` is forbidden), `dedup.py` (transaction-level dedup,
  contract 1.2), `units.py` (liters→gallons normalization, shared between
  dedup-key computation and the router so they can never drift apart),
  `address.py` (deterministic jurisdiction derivation — regex only, never
  a guess), `parsers/csv_parser.py` + `parsers/statement_parser.py`
  (deterministic; one parameterized vendor profile), `extraction/vision.py`
  (`ClaudeVisionExtractor` — real implementation, never called live in
  this build; see Flagged), `validators.py` (structural, sum, confidence,
  dedup), `router.py` (creates real `FuelRecord`/`ExpenseRecord` rows per
  the routing table), `intake.py` (`process_drop()` — register →
  extract → validate → route, quarantine on any failure), `README.md`.
- **`src/dispatch/ifta/`**: `db.py` (`rate_tables`, `ifta_worksheets`,
  `ifta_worksheet_lines`, `ifta_exceptions`), `rates.py`, `readonly.py`
  (genuine SQLite `mode=ro` connection — the actual source-immutability
  enforcement mechanism, not a convention), `worksheet.py` (computation
  spec 3.5, `WorksheetEngine`), `exceptions.py` (all ten detectors),
  `package.py` (draft → submit-for-approval → seal, via Lane B's real
  queue), `README.md`.
- **`tools/mileage_worksheet.py`** — manual `MileageRecord` entry.
- **The router is now built** (Packet C's old BLOCKED item) — creates
  real `fuel_records`/`expense_records` rows, cross-linked per Decision
  D1, category-validated against the frozen closed vocabulary.
- **213 tests pass across the whole repository** (Lanes A + B + C +
  conformance), including: golden regression for both the receipt
  pipeline (through routing, not just to `pending_routing`) and a
  hand-computed IFTA quarter; all ten IFTA exceptions firing from seeded
  data; dedup catching the receipt-vs-statement double; the reefer/DEF
  safety sweep (dedicated tests asserting no code path ever produces a
  `FuelRecord` for either); source-immutability proven behaviorally
  (`mode=ro` connection genuinely rejects writes) and statically (grep,
  same pattern as every other lane); audit completeness including
  quarantine flows.
- Manually smoke-tested the full chain end to end against a real
  throwaway sandbox: CSV drop → registered → routed to real
  `fuel_records`/`expense_records` → mileage entered via the tool →
  worksheet built → exception fired correctly (a single data point's
  implausible fleet MPG) → submitted for approval → approved → sealed →
  bundle written to `ARCHIVE\IFTA\<quarter>\`. This caught one real bug
  the automated suite didn't (see Flagged #5).

### Flagged (design decisions made without a live Mike decision)

1. **The vision extractor is never called live.** `ClaudeVisionExtractor`
   is a real implementation against the Anthropic API, but this build
   environment has no credentials for it, and a deterministic test suite
   shouldn't depend on a live external call regardless. "No API key
   configured" and "the call failed" both raise
   `VisionExtractionUnavailable`, which `intake.py` treats identically:
   quarantine the file. This is the literal stack-rationale behavior for
   an offline/outage condition, not a workaround.
2. **`document_date` at registration time, for freshly-dropped files, is
   the file's own filesystem mtime**, not the date printed on the
   document — because contract 1.4 requires archiving before extraction,
   and the real date is only knowable after extraction runs. The
   *trustworthy* business date lives on the resulting
   `FuelRecord`/`ExpenseRecord`'s `purchase_date`, extracted properly.
   Documented in `src/dispatch/receipt/README.md`.
3. **`ExpenseRecord.dedup_key`'s formula is Lane C's own choice.** The
   contract gives `FuelRecord`'s dedup formula verbatim but only lists
   `dedup_key` as "required" for `ExpenseRecord`, with no formula. Built
   `sha256(vendor_name|purchase_date|amount|line_description)` —
   analogous in spirit, not contract-specified.
4. **`derived_record_ids`-style append tables, generalized**: rather than
   ever issuing `UPDATE`/`DELETE` against `fuel_records`/`expense_records`,
   this lane simply never builds an update path for them at all — every
   quarantine happens *before* a record is created, not as a later
   correction to one. Same reasoning Lane A applied to `evidence_records`.
5. **A real bug the automated suite couldn't have caught**: `rates.py`'s
   functions originally assumed `WorksheetEngine.__init__` had already
   installed the `rate_tables` schema on a given connection. A manual
   end-to-end smoke test (inserting a rate before ever constructing an
   engine — an entirely reasonable calling order) hit
   `sqlite3.OperationalError: no such table: rate_tables`. Fixed by making
   `insert_rate`/`get_rate`/`distinct_versions_for` each call
   `install_schema()` themselves (idempotent). Every automated test
   happened to construct `ifta_engine` first, so this was invisible until
   the real walkthrough-style run — recorded here as the second concrete
   case (after Lane B's threading bug) of why running the actual thing
   matters, per `docs/reference/WALKTHROUGH_PROCEDURE_v1.md`.
6. **Exception detectors are best-effort against data this schema can
   actually represent.** A few (`miles_no_fuel_gap`,
   `late_arrival_closed_quarter`) are reasonable-but-not-uniquely-specified
   interpretations of their constitutional description, since the exact
   detection thresholds/logic aren't given verbatim the way the tax
   computation is. Documented per-function in `exceptions.py`'s
   docstrings; flagged here as judgment calls, not contract text.

### Deliberately Not Built

Per launch package §8 and the Librarian/Receipt/IFTA constitutions'
"explicitly not in Group 1" sections:

- **Trade Memory** — the one item still genuinely out of scope. Doctrine
  is adopted (`MEMORY_DOCTRINE_v1.md`), but adoption isn't authorization
  to build it, same reasoning every other lane has applied to itself. No
  pattern storage, no pattern reliance, anywhere in this lane's code.
- No QuickBooks connector, no tax-authority filing/correspondence/payment
  — permanent boundaries, not holds.
- No live vision-extraction call exercised (see Flagged #1) — the
  interface and real implementation exist; actually calling it live
  needs real credentials this build session was never given.
- Real IFTA per-jurisdiction rate data
  (`library_seed/RateTables/README.md`) — still not fabricated. This
  lane's golden quarter and all exception tests use clearly-tagged
  fixture rates (`source_version="fixture-v1"`), never installed via
  `tools/seed_library.py`. This blocks the golden-regression *gate*
  being callable "real," not this lane's build or merge.
- No persistent intake watcher/daemon — `process_drop()` is a callable a
  cron job or scheduled task invokes, matching every other lane's "no
  background process" pattern.

### Still outstanding before this lane can merge

- ~~**Mike's sandbox walkthrough**~~ — done. See
  `docs/lanes/C/WALKTHROUGH_REPORT_v1.md`: two documents dropped (one
  clean, one malformed) exercising register/extract/route and
  register/quarantine both; a live reefer-safety refusal check; mileage
  entered via the tool; a draft IFTA worksheet built from fixture rates;
  all ten exception detectors run (correctly flagging an implausible
  single-data-point fleet MPG); submit → approve → seal, with the sealed
  bundle confirmed on disk. Mike approved and instructed the merge;
  recorded in `docs/decisions/DECISION_LOG.md` ("Lane C merge approval —
  APPROVED, 2026-08-04").

## Session 2 (2026-08-04) — merge

`build/receipt-ifta` merged into `integration` following Mike's
walkthrough sign-off (above).

## Session 3 (2026-08-05) — vision extraction exercised live for real, one bug found and fixed

Branch: `build/ocr-fenced-json-fix`. Item 4 of Mike's 5-item work list
("OCR validation with real receipts") had been blocked all session —
no `ANTHROPIC_API_KEY` existed in any build environment used so far.
Mike supplied a real, disposable testing key directly in-session. Per
standing practice, the key was never written to any file (not the
sandbox config, not `.env`, nothing committed) — used only as a
transient environment variable for the lifetime of each live call, then
discarded. `anthropic` and `Pillow` (the latter dev-only, to synthesize
a test receipt image — no real scanned receipt existed in this build
environment) were installed locally for this session; `anthropic` is
now a real `requirements.txt` dependency (see below), `Pillow` is not.

### The live test that found the bug

A synthetic pump-receipt image (vendor, date, gallons, price, unit
number, driver, odometer, payment card, receipt number — every field a
real receipt would have) dropped into a throwaway sandbox's
`Intake/Drop`, run through the real `IntakePipeline.process_drop()`
with `ClaudeVisionExtractor` wired to a real API call. Result: the
model read every field correctly (`extraction_confidence: 0.97`,
independently confirmed by hand against the image), but the document
was quarantined anyway. Root cause: `_parse_response_text()` in
`src/dispatch/receipt/extraction/vision.py` called `json.loads(text)`
directly, and real Claude output wraps the JSON object in a ` ```json
... ``` ` markdown fence despite the prompt saying "no other text" —
`json.loads` threw immediately on the fence characters. This wasn't a
one-off flake; it would quarantine **every** real scanned receipt,
unconditionally. Evidence was still correctly registered, hashed, and
archived before the parse ever ran, and the quarantined file was
preserved intact in `Intake/Quarantine` — nothing was lost, but the
vision path itself was completely unusable until this fix.

### The fix

Added `_strip_markdown_fence()`: strips one leading/trailing ` ``` `
(with or without a `json` language tag) before `json.loads`, nothing
more — output that still isn't valid JSON after stripping still raises
`VisionExtractionUnavailable` exactly as before, so a genuinely broken
response still degrades to quarantine rather than being coerced into
parsing something it shouldn't. 5 new tests in `tests/lane_c/test_vision.py`,
including the exact fenced-JSON shape returned by the real live call,
reproduced verbatim as a regression fixture. Full suite: 457 passed (was
452).

### Re-verified live, after the fix

The identical receipt image, run through the identical pipeline again:
routed cleanly to a real `FuelRecord`/`ExpenseRecord`, no quarantine.
Every extracted field checked by hand against the source image and the
database row: vendor, TX jurisdiction (correctly derived from the
address), diesel, 112.4 gallons, $3.899/gal, $438.24 total, unit T-104,
driver, odometer, card last-4, receipt number, `extraction_confidence
0.97`, `review_status: auto` — all correct.

### `requirements.txt`

`anthropic>=0.40` is now uncommented — the comment's own stated
condition ("uncomment when Mike supplies a real API key and this
lane's extraction is actually exercised live") is now true. No
automated test in the suite makes a real API call; that stays a
live, human-run check by design, not something CI depends on.

## Session 4 (2026-08-05) — Archive Package: closing the evidence-refs gap

Branch: `build/archive-package-evidence-refs`. Item 3 of Mike's 5-item
work list ("Archive Package generation"). No blueprint document defines
"Archive Package" for IFTA specifically — investigation found
`package.py`'s `attempt_seal()` already writes a sealed bundle to
`ARCHIVE\IFTA\<quarter>\<id>.json`, and its own docstring has always
promised "worksheet + lines + evidence refs," but the actual code wrote
`{worksheet, lines, sealed_at, approved_by, approval_note}` — no
evidence refs at all. `ifta_worksheet_lines` were jurisdiction-level
aggregates only, with nothing linking a line's numbers back to the
specific `mileage_records`/`fuel_records`/`evidence_records` that
produced them. Mike confirmed this was the right scope ("close the
evidence-refs gap") before any code was written.

### Design

Refs are captured at `WorksheetEngine.build()` time, not re-derived at
seal time — if new mileage/fuel got entered between build and
submit/approve/seal (a real gap; that pipeline takes real time), a
seal-time re-query could link records that don't actually match the
frozen numbers. Capturing at build time keeps provenance exactly as
frozen as `total_net_tax` already is, matching `ifta_worksheet_lines`'
own documented "computation snapshot, INSERT-only" doctrine.

### Built

- `src/dispatch/ifta/db.py`: one new column,
  `ifta_worksheet_lines.related_record_ids TEXT NOT NULL DEFAULT '[]'`
  — mirrors the exact JSON-in-TEXT convention `ifta_exceptions
  .related_record_ids` already uses (`json.dumps` on write, `json.loads`
  on read), not a new pattern.
- `src/dispatch/ifta/worksheet.py`: `_aggregate_mileage`/
  `_aggregate_fuel` (shared by `build()` and `preview()`) now also
  collect which `mileage_record_id`/`fuel_record_id` contributed to
  each jurisdiction's totals, alongside the sums they already computed
  — purely additive provenance capture, computation spec 3.5's
  arithmetic itself untouched. `_compute_worksheet_lines` threads these
  into each line's new `related_record_ids` dict
  (`{"mileage_record_ids": [...], "fuel_record_ids": [...]}`).
  `preview()` gets the same shape for consistency (both functions stay
  identical) but still never persists anything.
- `src/dispatch/ifta/package.py`: `_resolve_line_evidence()` — for each
  sealed line, resolves `mileage_record_ids` into full mileage records
  (self-attested: unit, period, miles, source, `entered_by` — no source
  document to link, the record itself is the attestation) and
  `fuel_record_ids` into full fuel records plus their linked
  `evidence_records` row (`archive_path`, `file_hash`, `document_type`
  — the real registered document). A record that somehow doesn't
  resolve is skipped, not raised — nothing in this codebase deletes
  these rows, and a seal already granted by real approval must never be
  blocked by a bundling concern. `attempt_seal()`'s bundle now carries
  this as an `evidence` key per line.
- Tests: 3 new (1 in `tests/lane_c/test_worksheet.py` proving
  `related_record_ids` matches the real record IDs per jurisdiction; 2
  in `tests/lane_c/test_package.py` — one proving the sealed bundle's
  evidence resolves real mileage/fuel/evidence rows correctly by hand,
  one proving the "evidence row doesn't resolve" path degrades to
  `None` rather than raising, using the existing `insert_fuel_record`
  fixture's `'ev_fixture'` placeholder, which most tests never actually
  back with a real `evidence_records` row — the exact case this needed
  to handle gracefully). `tests/lane_c/conftest.py`'s
  `insert_mileage_record` now returns the id it inserts (additive;
  nothing captured its return value before). Full suite: 460 passed
  (was 457).
- `src/dispatch/ifta/README.md`: documented the bundle's real `evidence`
  shape and when it's captured.
- **Manual smoke test against the real pipeline** (throwaway sandbox,
  deleted after): real fuel CSV through the real `IntakePipeline`, a
  real mileage entry via `tools/mileage_worksheet.py`, a real rate, a
  real `build()`/`run_all_detectors()`/`submit_for_approval()`/
  `queue.approve()`/`attempt_seal()` pipeline. Independently confirmed
  by hand, reading the sealed bundle file directly: the fuel record's
  vendor, date, and gallons matched the source CSV exactly; its
  `evidence_record.archive_path` and `file_hash` were real, resolved
  values; the mileage record's `entered_by`/`miles`/`period` matched
  the CLI command exactly.

### Boundary — unchanged

Still exactly one file, same path (`ARCHIVE\IFTA\<quarter>\<id>.json`),
same trigger (`attempt_seal()`). No new artifact type, no new button,
no new write action — this is a correctness fix to an existing write
path. No current UI displays worksheet lines at all, so nothing visible
changed; only the bundle file's own content did.

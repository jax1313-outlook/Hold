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

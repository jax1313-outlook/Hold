# Lane A — Librarian Evidence Spine — NOTES

Branch: `build/librarian-spine`. Packet: `docs/lanes/A/LANE_A_LAUNCH_PACKAGE_v1.md`.

Update this file at the end of every Lane A session. Do not delete prior
entries — append.

## Session 1 (2026-08-04)

### Built

- `src/dispatch/common/`: `config.py` (schema validation via `jsonschema` +
  sandbox-refusal rule), `ids.py` (dependency-free ULID), `hashing.py`
  (SHA-256 file/bytes helpers), `db.py` (SQLite bootstrap: WAL, foreign
  keys, busy_timeout, and delete/update-revoking triggers on
  `evidence_records`, `evidence_children`, `audit_log`), `audit.py`
  (INSERT-only audit writer + a read helper for tools/tests).
- `src/dispatch/evidence/`: `interface.py` (`EvidenceSpine` class —
  `register` / `retrieve` / `link_children` exactly per contract 1.4),
  `index.py` (Library evidence index — one JSON file per record under
  `LIBRARY/EvidenceIndex/`), `README.md` (documents all three calls plus
  two design decisions, see "Flagged" below).
- `tools/init_roots.py`, `tools/seed_library.py` (idempotent by default,
  `--force` to overwrite), `tools/export_audit_rolls.py` (monthly JSONL,
  idempotent full-rewrite-per-month).
- `tests/conformance/`: real module outputs (register/retrieve/
  link_children results, audit entries, the hash-mismatch exception queue
  item) validated against `evidence_record.schema.json`,
  `audit_entry.schema.json`, and `queue_item.schema.json`; a fixture +
  round-trip check for `mileage_record.schema.json` since Lane A only
  bootstraps that table.
- `tests/lane_a/`: full golden regression + boundary refusal + audit
  completeness suite per launch package §6 (immutability, hash round-trip,
  register/retrieve fidelity, dedup with "never a second copy" verified at
  both the DB-row and archived-file level, retention-class defaulting, path
  mapping, a grep-based static check that no UPDATE/DELETE SQL statement
  against the three immutable tables exists anywhere in `src/dispatch`,
  sandbox-refusal, WAL concurrency, and tool-level tests for all three
  `tools/` scripts). 73 tests, all green.
- `requirements.txt` (`jsonschema`, `pytest` — dev/test tooling only, no
  runtime cloud dependency), `pytest.ini` (`pythonpath = src`), and the
  `__init__.py` files needed to make `dispatch` and `tests` importable
  packages. Removed the `.gitkeep` placeholders in every directory that now
  has real content (`src/dispatch/common`, `src/dispatch/evidence`, `tools`,
  `tests/conformance`, `tests/lane_a`).

### Flagged (design decisions made without a live Mike decision — recorded
here per the Failure Doctrine's "stop, quarantine, escalate" for anything
that reads as an open question, even though none of these blocked the work)

1. **`archive_path` storage format.** The schema's field description shows
   `ARCHIVE\Evidence\YYYY\MM\<evidence_id>.<ext>` — a description of the
   tier and Windows separator style the production target uses, not a
   literal template. What's actually stored is the path *relative to the
   configured archive root*, forward-slash-normalized
   (`Evidence/2026/08/<id>.txt`), which `pathlib` resolves correctly on
   both POSIX and Windows. This is the launch package's risk #1 mitigation
   (OS-agnostic path construction) applied literally. Documented in
   `src/dispatch/evidence/README.md`.
2. **Duplicate registration never mutates the original row.** "Returns the
   existing record flagged `duplicate_document`" is implemented by
   patching that field on the *returned dict only* — the stored row's
   `extraction_status` is set once at creation (`complete`) and never
   touched again, since no update code path exists on `evidence_records`,
   including for this case. A duplicate submission also makes zero new
   archive copies (checked by hash before any file I/O happens), not just
   zero new DB rows.
3. **`derived_record_ids` is a separate append-only table, not a mutated
   JSON column.** Growing that array via `link_children` would otherwise
   require an `UPDATE` against `evidence_records`, which has no update
   code path, permanently. `evidence_children` (`evidence_record_id,
   derived_record_id, linked_at`) holds the actual rows; the JSON array in
   a returned record is always computed by reading it back, ordered by
   SQLite's implicit `rowid` (insertion order) rather than `linked_at`,
   since two children linked in the same call share one
   second-resolution timestamp. Externally indistinguishable from the
   contract's shape; internally, the module surface has zero `UPDATE`/
   `DELETE` statements against `evidence_records` or `evidence_children` —
   verified by a dedicated grep-based test, not just code review.
4. **Read-only verification, not read-only assumption.** `register()`
   checks the archived file's mode bits directly after `chmod` rather than
   trusting the syscall succeeded (launch package risk #2). Tests do the
   same rather than attempting an actual write, because this container
   runs as root, which bypasses POSIX permission bits regardless of what
   the mode bits say — so "attempt a write and expect `PermissionError`"
   would not reliably test anything here.
5. **`document_date` is a hard requirement with no default.** Per Rule 11
   (No Fabrication), `register()` raises `ValueError` if `metadata` doesn't
   include it, rather than defaulting to `capture_date` or today's date.

None of the above required a decision on hold in
`docs/decisions/DECISION_LOG.md` — they're implementation choices inside
Lane A's own scope, made explicit here so the acceptance criterion "docs
match as-built" has something concrete to check against before merge.

### Deliberately Not Built

Per launch package §8's "must not" list and the Librarian constitution's
"Explicitly NOT in Group 1":

- No `fuel_records` or `expense_records` tables, and no code touching them
  — Lane C's router, out of Lane A's allowed files regardless of their
  FROZEN status.
- No truth promotion, retrieval governance, or Library metadata beyond the
  evidence index (`index.py` is a pointer store keyed by
  `evidence_record_id`, nothing more).
- No Trade Memory component (doctrine #14 is adopted, but adoption isn't
  authorization to build it — not in scope here).
- No Flask UI, receipt intake, IFTA worksheet engine, or reports (Lanes B/C/D).
- No production config anywhere in this repository; every test and the
  manual smoke test used throwaway sandbox roots under a temp directory,
  never `config/dispatch.config.json` (which still does not exist).
- No network calls anywhere in `src/dispatch/` or `tools/`.

### Still outstanding before this lane can merge

- ~~**Mike's sandbox walkthrough**~~ — done. See
  `docs/lanes/A/WALKTHROUGH_REPORT_v1.md`: register/retrieve/hash-verify
  plus a tamper-detection check, run 2026-08-04. Mike approved and
  instructed the merge in the same message; recorded in
  `docs/decisions/DECISION_LOG.md` ("Lane A merge approval — APPROVED,
  2026-08-04").
- The IFTA rate-table gap noted in `library_seed/RateTables/README.md` is
  unrelated to Lane A's gate and not blocking here.

## Session 2 (2026-08-04) — merge

`build/librarian-spine` merged into `integration` following Mike's
walkthrough sign-off (above). Standing procedure for future lane
walkthroughs (B, C, D) is now written down at
`docs/reference/WALKTHROUGH_PROCEDURE_v1.md`, per Mike's instruction to
run every future walkthrough the same way Lane A's was run.

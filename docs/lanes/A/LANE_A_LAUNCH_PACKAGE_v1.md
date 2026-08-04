# LANE A LAUNCH PACKAGE — Librarian Evidence Spine

Purpose: a launch-ready build packet for Lane A, current as of commit
`c20a2d0` (see `docs/HOLD_PRE_BUILD_v1.md`). Supersedes Packet A in
`docs/reference/DISPATCH_MATRIX_EXECUTION_PACKAGE_v1.md` for one reason:
all 14 approval items are now APPROVED (none were held on Lane A to
begin with, but the system-wide picture has changed since Packet A was
written — see §9).
Repository: `jax1313-outlook/hold`, branch `build/librarian-spine`.
Authority: Mike Zachary is final authority. This document contains no
implementation code and does not itself open a build session.

---

## 1. Mission

Build the evidence spine of Dispatch — archive-on-registration, hashing,
evidence indexing, retrieval — plus the shared plumbing (config, IDs,
hashing, database bootstrap, audit writer) every other lane will use.
This is the floor the system stands on; it merges first, and two other
lanes (B, C) stub against it until it does.

## 2. Files to create

All new files. Nothing in this list exists yet (`src/dispatch/**` and
`tools/**` currently hold only `.gitkeep` placeholders).

**`src/dispatch/common/`**
- `config.py` — loads and validates `dispatch.config.json` against
  `contracts/config.schema.json`; refuses to run if `environment=sandbox`
  and any root resolves under a production path.
- `ids.py` — ULID generator.
- `hashing.py` — SHA-256 utilities.
- `db.py` — SQLite bootstrap: WAL mode, foreign keys on, delete-revoking
  triggers on `evidence_records` and `audit_log`. Creates **only**
  `evidence_records`, `mileage_records`, `queue_items`, `audit_log` — see
  §9 on why `fuel_records`/`expense_records` are still out of scope.
- `audit.py` — audit writer, INSERT-only, per `contracts/audit_entry.schema.json`.

**`src/dispatch/evidence/`**
- `interface.py` — `register` / `retrieve` / `link_children` exactly per
  the interface behavior documented in
  `contracts/evidence_record.schema.json`'s `interface_note`.
- `index.py` — Library evidence index.
- `README.md` — documents the three interface calls (required deliverable).

**`tools/`**
- `init_roots.py` — creates the OPERATIONS/LIBRARY/ARCHIVE directory
  skeleton from config (per `DISPATCH_BUILD_BLUEPRINT_v1` Part 3.4).
- `seed_library.py` — installs `library_seed/**` into the configured
  LIBRARY root.
- `export_audit_rolls.py` — exports `audit_log` to
  `ARCHIVE\AuditRolls\YYYY-MM.jsonl` monthly.

**`tests/`**
- `tests/conformance/**` — the shared conformance suite, generated from
  `contracts/`. This is shared property every other lane's build will
  run; build it clean.
- `tests/lane_a/**` — the full Lane A test suite (§6).

## 3. Files to modify

- `docs/lanes/A/NOTES.md` — update at the end of the session: what was
  built, what was flagged, what was deliberately not built. Currently
  reads "nothing yet — seed only."

Nothing else. `contracts/**`, `docs/governance/**`, and every other
lane's directory are forbidden files (§8) — read, never write.

## 4. Dependencies

- Contracts only. No lane dependencies — Lane A is first and everyone
  else depends on it, not the reverse.
- Approved doctrines: #1 (storage mapping), #5 (failure doctrine), #6
  (deletion/retention), #10 (Librarian boundary clause) — all APPROVED
  2026-08-03.
- No stubs consumed.

## 5. Contract references

| Contract | File | Status | Relevance to Lane A |
|---|---|---|---|
| Config | `contracts/config.schema.json` | FROZEN v1.0 | Config loader validates against this; sandbox-refusal rule |
| Evidence Record | `contracts/evidence_record.schema.json` | FROZEN v1.0 | The record this lane creates and manages; interface behavior documented in its `interface_note` |
| Mileage Record | `contracts/mileage_record.schema.json` | FROZEN v1.0 | DB bootstrap creates this table (Lane C writes to it later) |
| Queue Item | `contracts/queue_item.schema.json` | FROZEN v1.0 | `retrieve()`'s hash-mismatch path enqueues an exception item — Lane A must know this shape even though it doesn't own the queue |
| Audit Entry | `contracts/audit_entry.schema.json` | FROZEN v1.0 | Every operation writes one, via the audit writer built here |

**Not needed by Lane A:** `fuel_record.schema.json`,
`expense_record.schema.json`, `expense_vocabulary.schema.json`. These are
now FROZEN (all four approval holds resolved 2026-08-04), but Lane A's
scope never included them — the DB bootstrap still creates only the four
tables above. Building `fuel_records`/`expense_records` tables or writing
to them is Lane C's router, not Lane A's evidence spine.

## 6. Test requirements

Per `DISPATCH_BUILD_MATRIX_AUDIT_v1` Section 7 and
`DISPATCH_MATRIX_EXECUTION_PACKAGE_v1` Packet A validation gates:

1. **Contract conformance** — outputs validate against
   `evidence_record.schema.json` and `audit_entry.schema.json`, byte-for-byte
   on shared fixtures. This suite is generated once here and reused by
   every later lane.
2. **Golden regression:**
   - Immutability — modify-after-archive **fails**.
   - Hash integrity round-trip.
   - Register → retrieve fidelity.
   - Duplicate-hash registration returns the existing record flagged
     `duplicate_document` (never a second copy).
   - Retention class defaulting.
   - Audit-entry-per-operation.
   - Path mapping honored — writes land only under configured roots.
3. **Boundary refusal (negative tests):**
   - No update/delete code path exists on archived files,
     `evidence_records`, or `audit_log` — verified by test **and** by
     grep of the module surface (no `UPDATE`/`DELETE` SQL statements
     against those tables anywhere in the codebase).
   - Sandbox-mode production-root refusal fires.
4. **Audit completeness** — every action in the test run produced a
   well-formed audit entry; sampled and verified.

## 7. Acceptance criteria (Definition of Done)

- All Lane A tests green, including every negative test in §6.
- Conformance suite green.
- Every operation writes a valid audit entry (contract 1.6 shape).
- `src/dispatch/evidence/README.md` documents `register` / `retrieve` /
  `link_children`.
- `docs/lanes/A/NOTES.md` updated: built / flagged / deliberately not
  built.
- **Mike's walkthrough:** register a real document in sandbox, retrieve
  it, verify the hash. No merge on green checks alone.
- **Docs match as-built:** if anything built diverges from
  `LIBRARIAN_CONSTITUTION_v1.md` or this launch package, the divergence
  is resolved in the documents before merge — the documents are the law.
- Branch `build/librarian-spine` ready for `integration` (Lane A merges
  first).

## 8. Expected deliverables

Working `dispatch.common` and `dispatch.evidence` packages; the three
tools (`init_roots.py`, `seed_library.py`, `export_audit_rolls.py`); the
shared conformance suite; Lane A tests green; `README.md` for the three
interface calls; updated `docs/lanes/A/NOTES.md`; branch
`build/librarian-spine` ready for `integration`.

**Forbidden files** (touching these is a failed gate, even if the change
is correct): `contracts/**` (read-only) · `config/dispatch.config.json`
(production — must not exist yet) ·
`src/dispatch/{queue,receipt,ifta,reports}/**` ·
`library_seed/Constitutions/**` (doctrine content is Mike's) · anything
outside this repository.

**Must not:** write any update/delete path for archived data; hardcode
any filesystem root; make network calls; build truth promotion,
retrieval governance, or Library metadata beyond the evidence index
(Truth Governance is a separate, later lane); expand scope (flag ideas
in `NOTES.md` instead).

## 9. What changed since Packet A was written

Packet A (`docs/reference/DISPATCH_MATRIX_EXECUTION_PACKAGE_v1.md`) was
written when #2/#3/#4/#14 were still held. Lane A never touched any of
them, so its *scope* is unchanged. What changed:

- All 14 approval items are now APPROVED (`docs/decisions/DECISION_LOG.md`).
- `fuel_record.schema.json` and `expense_record.schema.json` are now
  FROZEN (previously `.DRAFT.json`). A Lane A session reading old
  language might assume these tables are still excluded *because they're
  unapproved* — they are not. They're excluded because they're **out of
  this lane's allowed files**, same as `queue`, `receipt`, `ifta`, and
  `reports` directories are. Scope boundary, not approval boundary.
- `DISPATCH_BASE_CONSTITUTION_v1.md`'s Hard Approval Gates section and
  `MEMORY_DOCTRINE_v1.md`'s Trade Memory section are now filled in
  (previously reserved/empty). Neither changes what Lane A builds.

## 10. Risks

1. **Windows path handling.** `archive_path` uses backslashes and dated
   subfolders (`ARCHIVE\Evidence\YYYY\MM\`); a build session working in a
   POSIX-first mindset could construct paths that break on the actual
   Windows production target even though sandbox tests pass on Linux/Mac.
   Mitigation: use `pathlib`/OS-agnostic path construction throughout;
   test path construction logic, not just outcomes, against both
   separator styles.
2. **Read-only attribute failure.** Setting a file read-only after
   archiving can fail silently on some filesystems/permission
   configurations, leaving a file that's "immutable" only by code
   convention, not OS enforcement. Mitigation: verify the attribute took
   effect as part of the register() test, don't just call the syscall
   and assume.
3. **SQLite WAL + concurrent access.** Lane B and C will later run
   against the same `dispatch.db` (Lane A's bootstrap). If WAL mode or
   busy-timeout handling is wrong, later lanes hit intermittent lock
   errors that look like their bugs, not Lane A's. Mitigation: test
   concurrent read/write explicitly, not just single-threaded happy path.
4. **Stub drift.** Lane B and C build against
   `tests/stubs/evidence_stub.py` / `audit_stub.py` (their files, not
   Lane A's) with signatures matching Lane A's real interface. If Lane
   A's actual interface ships with a subtly different signature than
   what's documented, both other lanes' stubs silently diverge from
   reality until integration. Mitigation: `README.md` (§2) must be
   exact, and the conformance suite should exercise the documented
   interface signature directly.
5. **seed_library.py overwrite risk.** Re-running the seeding tool
   against a LIBRARY root that already has content (e.g. re-running in
   an existing sandbox) could silently overwrite. Mitigation: make it
   idempotent and non-destructive by default (skip existing, or require
   an explicit `--force`).
6. **Scope creep into truth promotion.** The evidence index and Library
   promotion workflow are adjacent, and it's tempting to build "just a
   little" retrieval governance while already in `src/dispatch/evidence/`.
   Mitigation: this is the single most likely forbidden-file/scope
   violation for this lane — treat §8's "must not" list as a hard stop,
   not a suggestion.

## 11. Rollback plan

No data or code exists yet on `build/librarian-spine` beyond the seed
commits it shares with every other branch — there is nothing to unwind
in production or in any other lane's work, because no other lane has
started and no sandbox data has been written.

If a Lane A session needs to be abandoned or restarted:

1. Before abandoning, write whatever is known to
   `docs/lanes/A/NOTES.md` (built / flagged / deliberately not built) so
   the next session doesn't repeat dead ends.
2. `git reset --hard` (or simply re-branch)
   `build/librarian-spine` back to `integration`'s current tip
   (currently `c20a2d0`, identical across all branches) — this discards
   only Lane A's in-progress work, nothing shared.
3. Delete any sandbox directories the aborted session created on disk
   (`D:\DispatchSandbox\...` per `config/sandbox.config.json`) — these
   are outside the repository and outside version control, so they don't
   roll back with git.
4. No `integration` or `main` rollback is ever needed at this stage:
   Lane A has not merged, so those branches are unaffected by anything
   that happens on `build/librarian-spine`.
5. If a merge *had* already happened and needed reversal: back out of
   `integration` cleanly (per `DISPATCH_BUILD_MATRIX_AUDIT_v1` Section 8,
   "a failed merge backs out cleanly") and re-open Lane A from the
   pre-merge commit. Not applicable yet — recorded here for completeness
   since this is a launch package, not just a status snapshot.

## 12. Ready-to-run build prompt

```
You are building LANE A of Dispatch Matrix Group 1 in the Hold repository,
branch build/librarian-spine. You are a bounded build session.

STATUS (2026-08-04): all 14 approval items are APPROVED. None were ever
held for Lane A — this lane has been fully unblocked since the repository
was seeded. If any thread of work seems to need a decision that isn't in
docs/decisions/DECISION_LOG.md's Resolved section, STOP that thread and
record it in docs/lanes/A/NOTES.md — do not assume.

READ FIRST: docs/HOLD_PRE_BUILD_v1.md (current baseline); this launch
package in full; docs/governance/DISPATCH_BASE_CONSTITUTION_v1.md;
docs/governance/LIBRARIAN_CONSTITUTION_v1.md;
docs/reference/DISPATCH_BUILD_BLUEPRINT_v1.md Parts 1, 3, 4.1, 5;
contracts/evidence_record.schema.json, mileage_record.schema.json,
queue_item.schema.json, audit_entry.schema.json, config.schema.json.

BUILD: src/dispatch/common/ — config loader (validates config; REFUSES to
run if environment=sandbox and any root resolves under a production D:\
path), ULID, SHA-256 utils, SQLite bootstrap (WAL, FKs, delete-revoking
triggers on evidence_records and audit_log; create ONLY tables whose
build scope includes them: evidence_records, mileage_records,
queue_items, audit_log — do NOT create fuel_records or expense_records
tables; those are Lane C's router, out of THIS lane's allowed files, not
unapproved), audit writer (INSERT-only) per contract 1.6.
src/dispatch/evidence/ — register/retrieve/link_children exactly per the
interface_note in contracts/evidence_record.schema.json: register
archives the original under ARCHIVE\Evidence\YYYY\MM\ BEFORE any other
processing, sets read-only, hashes, dedups by hash (duplicate ⇒ return
existing record flagged duplicate_document), writes the Library index
entry; retrieve verifies hash and raises + enqueues an exception queue
item on mismatch; link_children appends derived ids. There is NO update
and NO delete in this interface, permanently.
tools/init_roots.py, seed_library.py, export_audit_rolls.py.
tests/conformance/ generated from contracts/ (this suite is shared
property — build it clean), tests/lane_a/ per this launch package §6.

MUST NOT: edit contracts/ or docs/governance/; create production config;
touch src/dispatch/{queue,receipt,ifta,reports}; write any update/delete
path for archived data; hardcode any filesystem root; make network
calls; build truth promotion or retrieval governance; expand scope (flag
ideas in NOTES.md instead).

DONE WHEN: all Lane A + conformance tests green including the negative
tests (modify-after-archive FAILS, sandbox refusal FIRES); every
operation audited; src/dispatch/evidence/README.md and
docs/lanes/A/NOTES.md written; branch ready for integration. Mike's
sandbox walkthrough (register/retrieve/verify a real document) still
required before merge — green tests alone are not sufficient.
```

---

*End of LANE_A_LAUNCH_PACKAGE_v1. Documentation only; no implementation
code; does not itself open a build session.*

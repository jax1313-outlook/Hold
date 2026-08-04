# LANE C LAUNCH PACKAGE — Receipt → IFTA Chain

Purpose: a launch-ready build packet for Lane C, current as of commit
`5357bb7` on `integration` (Lanes A and B merged). Supersedes Packet C in
`docs/reference/DISPATCH_MATRIX_EXECUTION_PACKAGE_v1.md` for reasons that
are, this time, substantial rather than cosmetic — see §9. Packet C was
written as "partially blocked;" it no longer is.
Repository: `jax1313-outlook/hold`, branch `build/receipt-ifta`.
Authority: Mike Zachary is final authority. This document contains no
implementation code and does not itself open a build session.

---

## 1. Mission

Build the highest-value chain in Dispatch: intake and extraction of
receipts and statements, classification into Fuel and Expense Records
with transaction-level dedup, routing per the adopted routing table, and
the IFTA Agent's worksheet/exception/package pipeline built against real
fuel and mileage data. "A receipt is a container of business
transactions" is the load-bearing design decision this lane implements.

## 2. Files to create

All new files. Nothing in this list exists yet (`src/dispatch/receipt/**`,
`src/dispatch/ifta/**`, `tests/lane_c/**`, `tests/golden/**` currently
hold only `.gitkeep` placeholders).

**`src/dispatch/receipt/`**
- `intake.py` — `process_drop(config)`: scans `OPERATIONS\Intake\Drop`
  once per call (no persistent watcher/daemon in this lane — see §10
  risk #1 for why), registers each file via Lane A's real
  `EvidenceSpine.register()` FIRST, moves the source file to
  `Intake\Processing` on success or `Intake\Quarantine` + an exception
  `queue_item` on registration failure.
- `parsers/csv_parser.py` — deterministic CSV export parser.
- `parsers/statement_parser.py` — one parameterized fuel-card statement
  format (vendor profile as data, not a guess).
- `extraction/vision.py` — a `VisionExtractor` interface plus a real
  `ClaudeVisionExtractor` implementation for scanned/photographed
  receipts, and the "no credentials configured ⇒ quarantine to review
  queue" degradation path required by the stack rationale ("extraction
  degrades to the review queue when offline"). See §10 risk #2.
- `validators.py` — structural check, sum validation (lines + tax =
  total, else exception), transaction-level dedup (`dedup_key` per
  contract 1.2 — collision ⇒ suppress + flag, never drop), confidence
  threshold ⇒ line-level quarantine.
- `router.py` — converts validated, classified line items into real
  `FuelRecord`/`ExpenseRecord` rows per the routing table
  (`RECEIPT_CONSTITUTION_v1`): propulsion fuel ⇒ both, cross-linked;
  reefer-flagged fuel ⇒ `ExpenseRecord` only, category `reefer_fuel`,
  excluded from IFTA gallons; DEF ⇒ `ExpenseRecord` only, category
  `def`, never IFTA under any circumstance; everything else ⇒
  `ExpenseRecord` in its routing-table category. Category validated
  against `contracts/expense_vocabulary.schema.json`; an unclassifiable
  line quarantines, the rest of the document routes normally.
- `README.md` — documents the pipeline stages and the router's routing
  table implementation, same pattern as Lanes A/B's module READMEs.

**`src/dispatch/ifta/`**
- `worksheet.py` — the computation engine, exactly per spec 3.5
  (`fleet_mpg`, per-jurisdiction `taxable_gallons`/`net_tax`), reading
  rates only from a versioned `rate_tables` table, recording which
  version a worksheet used.
- `exceptions.py` — all ten exception detectors (`IFTA_CONSTITUTION_v1`).
- `package.py` — quarterly package builder: `DRAFT` status, seal-on-
  approval via Lane B's real queue (`QueueStore`), sealing writes the
  bundle (worksheet + records + evidence refs) to `ARCHIVE\IFTA\<quarter>\`.
- `README.md` — documents the worksheet engine, exception list, and the
  draft→seal lifecycle.

**`tools/mileage_worksheet.py`** — manual-entry tool writing
`MileageRecord` rows (`source=manual_worksheet`).

**`tests/`**
- `tests/lane_c/**` — the full Lane C test suite (§6).
- `tests/golden/receipts/**` — fixture "golden" receipts + expected
  classified-line output, constructed by this lane (not real customer
  documents — see §10 risk #4 on why golden-set *blessing* is a separate,
  later step from golden-set *existence*).
- `tests/golden/ifta/**` — one hand-computed quarter, built from **fixture**
  rate-table data, clearly marked as fixture (see §10 risk #3 and
  `library_seed/RateTables/README.md` — real rates are a gate-blocking
  gap, not a build-blocking one).

## 3. Files to modify

- `docs/lanes/C/NOTES.md` — update at the end of the session, with an
  explicit section for anything genuinely parked (Trade Memory only, per
  §9 — nothing else remains blocked).
- `requirements.txt` — add whatever the real vision-extraction
  implementation needs (e.g. `anthropic`) — dev dependency for the
  interface to exist; no live call happens in this lane's own test suite
  (see §10 risk #2).

Nothing else. `contracts/**`, `docs/governance/**`,
`src/dispatch/{common,evidence,queue,reports}/**`, and every other lane's
directory are forbidden files (§8) — read, never write.

## 4. Dependencies

- Contracts 1.1 (Evidence), 1.2 (FuelRecord, ExpenseRecord, MileageRecord
  — all now FROZEN, not draft), 1.3 (Queue), 1.4 (Evidence interface),
  1.5 (closed vocabulary), 1.6 (Audit). Computation spec 3.5.
- Approved doctrines: #5 (failure), #12 (Receipt boundary), #13 (IFTA
  boundary) — all APPROVED 2026-08-03; #2 (dual-record fuel), #3 (closed
  vocabulary) — APPROVED 2026-08-04, now load-bearing for this lane
  specifically (see §9).
- **Lane A and Lane B, for real** (not stubs): `dispatch.common.audit`,
  `dispatch.common.db`, `dispatch.evidence.interface.EvidenceSpine`
  (register/retrieve), `dispatch.queue.store.QueueStore` (create,
  transitions). Both merged into `integration` before this branch was
  even created — `build/receipt-ifta` was fast-forwarded to `integration`'s
  tip specifically so this is true from the first commit.

## 5. Contract references

| Contract | File | Status | Relevance to Lane C |
|---|---|---|---|
| Fuel Record | `contracts/fuel_record.schema.json` | FROZEN v1.0 | The router creates these; the IFTA engine reads them |
| Expense Record | `contracts/expense_record.schema.json` | FROZEN v1.0 | The router creates these |
| Expense Vocabulary | `contracts/expense_vocabulary.schema.json` | FROZEN v1.0 | Category validation — closed list, never extended in code |
| Evidence Record | `contracts/evidence_record.schema.json` | FROZEN v1.0 | Every intake document registers through this first |
| Mileage Record | `contracts/mileage_record.schema.json` | FROZEN v1.0 | `tools/mileage_worksheet.py` writes these; the IFTA engine reads them |
| Queue Item | `contracts/queue_item.schema.json` | FROZEN v1.0 | Every exception, quarantine, and package-approval request is one |
| Audit Entry | `contracts/audit_entry.schema.json` | FROZEN v1.0 | Every operation writes one, via Lane A's real audit writer |

## 6. Test requirements

Per `DISPATCH_BUILD_BLUEPRINT_v1` Section 5 and Packet C's validation
gates (updated: no stubs remain relevant):

1. **Contract conformance** — every `FuelRecord`/`ExpenseRecord`/
   `MileageRecord`/`QueueItem` this lane produces validates against its
   schema; extend the shared `tests/conformance/` suite.
2. **Golden regression:**
   - The golden receipt set's extractions match blessed output **through
     routing** (further than the old Packet C's "classified-line stage"
     ceiling, since the router is no longer blocked).
   - The hand-computed golden quarter reproduces exactly from fixture fuel
     + entered mileage data.
   - All ten IFTA exception types fire from seeded data.
   - Dedup catches the receipt-vs-statement double (the container
     model's whole reason for existing).
   - Sum-validation catches seeded mismatches.
3. **Boundary refusal (negative tests):**
   - No GL codes, deductibility, tax treatment, or reimbursement status
     field exists anywhere on `ExpenseRecord` (schema already forbids it
     — test that nothing in this lane's code tries to add one anyway).
   - No vocabulary list embedded in code outside the one read from
     `contracts/expense_vocabulary.schema.json` / the Library copy — an
     unclassifiable category is rejected, never silently accepted.
   - IFTA cannot mutate a source `FuelRecord`/`MileageRecord` — read-only
     access pattern, verified by a negative test in the same style as
     Lane A's grep-based immutability tests.
   - No auto-resolution of any exception type.
   - No file/submit/transmit capability exists anywhere (no QuickBooks
     call, no tax-authority endpoint — the only sanctioned outbound call
     in this whole lane is the vision extractor, and only when explicitly
     configured with credentials).
   - `pending_routing` items cannot silently expire — no timer-based
     transition, same pattern as Lane B's no-timer test.
4. **Audit completeness**, including quarantine flows specifically (not
   just the happy path).

## 7. Acceptance criteria (Definition of Done)

- All Lane C tests green, including every negative test in §6.
- Conformance suite (extended, not duplicated) green.
- Every operation writes a valid audit entry.
- `src/dispatch/receipt/README.md` and `src/dispatch/ifta/README.md`
  written.
- `docs/lanes/C/NOTES.md` updated: built / flagged / deliberately not
  built, with an explicit note that Trade Memory is the only thing still
  parked and why.
- **Mike's walkthrough**, run per `docs/reference/WALKTHROUGH_PROCEDURE_v1.md`:
  drop one real (or realistic fixture) document in a sandbox, watch it
  register → extract → validate → route into real Fuel/Expense records,
  and produce a draft IFTA worksheet from fixture rate data + manually
  entered mileage.
- **Docs match as-built.**
- Branch `build/receipt-ifta` ready for `integration` (merges after A and
  B — already true structurally).
- **Not required for this lane's merge, but required before its golden-
  regression gate can be called fully passed:** real per-jurisdiction IFTA
  rate data (`library_seed/RateTables/README.md`). This is a pre-existing,
  explicitly non-fabricated gap, not new to this launch package.

## 8. Expected deliverables

Working `dispatch.receipt` (intake, parsers, vision extraction interface,
validators, router — emitting real `FuelRecord`/`ExpenseRecord` rows) and
`dispatch.ifta` (worksheet engine, exception detectors, package
builder/seal) packages; `tools/mileage_worksheet.py`; golden suites;
`docs/lanes/C/NOTES.md`; branch `build/receipt-ifta` ready for
`integration`.

**Forbidden files:** `contracts/**` · `src/dispatch/{common,evidence,queue,reports}/**`
(import, never edit) · production config · any Trade Memory storage or
logic (doctrine adopted, building it is not authorized by that alone —
same reasoning Lane A applied to itself) · anything outside this
repository.

**Must not:** call QuickBooks or any tax-authority endpoint; file, pay,
or correspond with a tax authority; mutate a source Fuel/Mileage record;
auto-resolve any exception; embed a category vocabulary anywhere except
by reading the one frozen source; build Trade Memory; expand scope.

## 9. What changed since Packet C was written

This is the substantial version of this section. Packet C
(`docs/reference/DISPATCH_MATRIX_EXECUTION_PACKAGE_v1.md`, written
2026-08-03) was explicitly "partially blocked" — its BLOCKED section
named the router, `fuel_records`/`expense_records` table creation,
category validation, and `ExpenseRecord` emission as all awaiting #2/#3.

**All of that is now unblocked.** #2 (dual-record fuel) and #3 (closed
expense vocabulary) were APPROVED 2026-08-04
(`docs/decisions/DECISION_LOG.md`). `RECEIPT_CONSTITUTION_v1.md` and
`IFTA_CONSTITUTION_v1.md` were updated at that time to say so explicitly:
their own "Formerly-HELD items" sections now read "not yet built," not
"held." `fuel_record.schema.json` and `expense_record.schema.json` are
FROZEN v1.0, not draft. A Lane C session reading only the old Packet C
language would build roughly half of what's actually authorized —
stopping at `pending_routing` instead of building the router, and
treating the FuelRecord/ExpenseRecord schemas as provisional when they
are not.

Two things are unchanged:
- **#14 (Trade Memory)** is adopted as doctrine but, per the same logic
  Lane A applied to itself, adoption of the doctrine is not authorization
  to build the component. This launch package treats Trade Memory as
  deliberately out of scope, not blocked.
- **The real IFTA rate-table gap** is not a decision at all — it's data
  nobody has supplied yet (`library_seed/RateTables/README.md`). It
  blocks the golden-regression *gate*, not this lane's *start*, exactly as
  it was scoped in `HOLD_PRE_BUILD_v1.md` §7.

**Also unchanged from Packet C, still true:** the LLM-vision extraction
requirement for scanned receipts, and the stack rationale's explicit
sanctioning of that one network call as the system's only outbound
dependency.

**Newly true, not addressed by Packet C at all:** Lane A and Lane B have
both merged into `integration`. Every "stub until Lane A/B merges" clause
in the old packet is moot — this lane imports the real modules from its
first commit.

## 10. Risks

1. **"Intake watcher" as a stateless scan, not a persistent daemon.**
   Packet C's language ("intake watcher on `Intake\Drop`") suggests a
   long-running filesystem-watching process. This launch package instead
   scopes it as `process_drop(config)`: a function that scans the folder
   once per call and is idempotent to call repeatedly (via cron, a manual
   trigger, or a scheduled task outside this codebase). Mitigation for
   the risk this undersells the requirement: if Mike wants a real
   persistent watcher process, that's an operational wrapper around this
   function, not a different function — flag in `NOTES.md` if this
   reading turns out to be wrong, rather than guessing at a daemon
   architecture nothing else in this codebase resembles (no other lane
   runs a background process).
2. **The vision extractor is the one place this codebase makes a network
   call, and this lane has no real API credentials to test it against.**
   Mitigation, not a workaround: build `VisionExtractor` as an interface;
   `ClaudeVisionExtractor` is a real implementation that reads its API key
   from config/environment (never hardcoded) and is exercised in tests
   only via mocking the HTTP boundary, never a live call. Absence of a
   configured key isn't a build gap to paper over — the stack rationale
   already specifies the exact required behavior for that case:
   "extraction degrades to the review queue when offline." A scanned
   document with no working vision path quarantines to the review queue,
   which is simultaneously the correct production behavior for a genuine
   outage and the correct sandbox/test behavior for "no key configured."
   One code path, two occasions to use it.
3. **Fixture rate data must never be mistaken for real rate data.**
   `library_seed/RateTables/README.md` already establishes this — fixture
   rows live in test fixtures only, tagged unambiguously (e.g. a
   `source_version` like `"fixture-v1"` that could never be confused with
   a real quarterly publication citation), never installed into
   `LIBRARY\RateTables\` by `seed_library.py`.
4. **Golden-set existence vs. golden-set blessing.** This lane can and
   should construct `tests/golden/receipts/**` fixtures itself (per the
   Hold Seed Package's own rule that golden sets "may start empty; they
   must be non-empty before the gate, not the lane's start"), but
   "Mike blesses expected outputs" is his review, not this lane's
   self-certification. Label self-constructed fixtures as exactly that in
   `NOTES.md` — constructed-for-testing, not yet blessed — so nobody
   mistakes a green test suite for Mike's sign-off on extraction
   accuracy.
5. **Scope size.** This is the largest single lane by a wide margin —
   intake, two parsers, a network-capable extractor, four validator
   types, a routing table with several distinct branches, a ten-detector
   exception engine, and a seal-on-approval package builder. Mitigation:
   build and test the receipt pipeline (intake → extraction → validation
   → routing) as a complete, independently-testable stage before starting
   the IFTA engine, rather than interleaving both — matches how this
   session paced Lanes A and B as complete units rather than partial
   slices.
6. **Reefer/DEF exclusion is easy to get backwards.** The router's most
   safety-critical branch: reefer-flagged fuel and DEF must never reach
   IFTA propulsion gallons, under any circumstance, even though they're
   both "fuel" in casual language. Mitigation: a dedicated negative test
   asserting no code path produces a `FuelRecord` for either category,
   not just a positive test that the common case works.

## 11. Rollback plan

`build/receipt-ifta` currently contains nothing beyond what it shares
with `integration` (Lanes A and B, merged) — there is no Lane C-specific
work to lose yet.

If a Lane C session needs to be abandoned or restarted:

1. Before abandoning, write whatever is known to `docs/lanes/C/NOTES.md`.
2. `git reset --hard` (or re-branch) `build/receipt-ifta` back to
   `integration`'s current tip — discards only Lane C's in-progress work.
3. Delete any sandbox directories the aborted session created on disk —
   outside the repository, outside version control.
4. No `integration`/`main` rollback needed unless a Lane C merge *had
   already happened* — not applicable yet.

## 12. Ready-to-run build prompt

```
You are building LANE C of Dispatch Matrix Group 1 in the Hold repository,
branch build/receipt-ifta. You are a bounded build session.

STATUS (2026-08-04): all 14 approval items are APPROVED. Lanes A and B have
MERGED into integration -- this branch's own history already contains
both merges. dispatch.common.*, dispatch.evidence.interface, and
dispatch.queue.store are real, tested, walked-through modules. Import and
use them directly; no stubs. #2 and #3 are resolved, which means -- unlike
the OLD Packet C in docs/reference/DISPATCH_MATRIX_EXECUTION_PACKAGE_v1.md
-- the router, fuel_records/expense_records table creation, and category
validation are ALL authorized and in scope now. Read
RECEIPT_CONSTITUTION_v1.md and IFTA_CONSTITUTION_v1.md directly; do not
rely on the old packet's BLOCKED section, which is stale. The only thing
still genuinely out of scope is Trade Memory (#14 is adopted as doctrine,
not as authorization to build it).

READ FIRST: docs/lanes/C/LANE_C_LAUNCH_PACKAGE_v1.md in full;
docs/governance/RECEIPT_CONSTITUTION_v1.md;
docs/governance/IFTA_CONSTITUTION_v1.md;
docs/reference/DISPATCH_BUILD_BLUEPRINT_v1.md Parts 1, 3.5, 4.3, 5;
contracts/fuel_record.schema.json, expense_record.schema.json,
expense_vocabulary.schema.json, mileage_record.schema.json,
evidence_record.schema.json, queue_item.schema.json;
src/dispatch/evidence/README.md and src/dispatch/queue/README.md (the
real interfaces you'll call into); library_seed/RateTables/README.md (the
rate-data gap -- fixture data only, never presented as real);
docs/reference/WALKTHROUGH_PROCEDURE_v1.md.

BUILD -- RECEIPT (src/dispatch/receipt/): process_drop(config) scans
Intake\Drop once per call (no persistent daemon -- see launch package
risk #1); every file registers via dispatch.evidence.interface.EvidenceSpine
.register() FIRST; registration failure -> Intake\Quarantine + an
exception queue_item via dispatch.queue.store.QueueStore. Parser registry:
deterministic CSV parser; one parameterized fuel-card statement format.
A VisionExtractor interface + a real Claude-vision implementation for
scans, reading its API key from config/environment, never hardcoded --
no key configured or a call failure both degrade to "quarantine to review
queue," per the stack's own offline-degradation rule (this is the correct
behavior, not a gap to work around). Every path passes deterministic
validators: structural check, sum validation (lines+tax=total else
exception), transaction dedup (contract 1.2's dedup_key -- collision =>
suppress+flag, never drop), confidence threshold (below => line-level
quarantine, rest of document proceeds). The router converts validated,
classified line items into real FuelRecord/ExpenseRecord rows per
RECEIPT_CONSTITUTION_v1's routing table -- propulsion fuel => both,
cross-linked; reefer fuel => ExpenseRecord only, excluded from IFTA
gallons; DEF => ExpenseRecord only, never IFTA, ever; category validated
against the frozen closed vocabulary, unclassifiable => quarantine that
line, route the rest of the document normally.

BUILD -- IFTA (src/dispatch/ifta/): tools/mileage_worksheet.py writing
MileageRecords (source=manual_worksheet). Worksheet engine exactly per
blueprint 3.5 (fleet_mpg, per-jurisdiction taxable_gallons/net_tax),
reading rates ONLY from a versioned rate_tables table, recording the
version used. Fixture rate data for testing is allowed and expected --
tag it unambiguously as fixture (e.g. source_version "fixture-v1"),
never install it via seed_library.py. All ten exception detectors from
IFTA_CONSTITUTION_v1, each terminating in the queue. Quarterly package
builder: DRAFT status, seal-on-approval via dispatch.queue.store.QueueStore,
sealing writes the bundle to ARCHIVE\IFTA\<quarter>\.

MUST NOT: edit contracts/ or src/dispatch/{common,evidence,queue,reports}/;
call QuickBooks or any tax-authority endpoint; file, pay, or correspond
with a tax authority; mutate a source Fuel/Mileage record (read-only
access, negative test); auto-resolve any exception; build Trade Memory;
embed a category vocabulary outside the one frozen source; expand scope.

DONE WHEN: golden receipt set matches through routing (not just the
classified-line stage); hand-computed golden quarter (fixture rates)
reproduces exactly; all ten exceptions fire from seeded data; dedup
catches the receipt-vs-statement double; reefer/DEF-never-reaches-IFTA
has a dedicated negative test; boundary refusal tests green; audit
completeness verified including quarantine flows; conformance suite
(extended) green; src/dispatch/receipt/README.md and
src/dispatch/ifta/README.md written; docs/lanes/C/NOTES.md written with
Trade Memory as the only explicitly parked item; branch ready. Mike's
walkthrough (drop a document, watch it register/extract/validate/route,
produce a draft worksheet) still required before merge -- green tests
alone are not sufficient, and note in NOTES.md that self-constructed
golden fixtures are not the same as Mike's blessing of them.
```

---

*End of LANE_C_LAUNCH_PACKAGE_v1. Documentation only; no implementation
code; does not itself open a build session.*

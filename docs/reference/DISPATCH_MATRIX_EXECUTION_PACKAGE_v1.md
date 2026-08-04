# DISPATCH_MATRIX_EXECUTION_PACKAGE_v1

Purpose: four independent, session-ready build packets for Matrix Group 1, derived from DISPATCH_BUILD_BLUEPRINT_v1 and the approval status of 2026-08-03.
Repository: all implementation occurs in the **Hold repository**. No build session touches production D:\ roots — sandbox configuration only, until Mike cuts over after merge 5.
Authority: Mike Zachary is final authority. This package contains no implementation code.

## APPROVAL STATUS THIS PACKAGE RESPECTS

APPROVED: #1 storage mapping · #5 failure doctrine · #6 deletion/retention · #7–#13 all seven worker boundary clauses. Also in force (not held): queue item contract 1.3, archive/evidence interface 1.4, audit entry format 1.6, EvidenceRecord and MileageRecord schemas, IFTA computation spec 3.5.
HELD: **#2** dual-record fuel · **#3** closed expense vocabulary · **#4** hard approval gates · **#14** Trade Memory doctrine.
Consequences applied throughout: FuelRecord/ExpenseRecord schemas are NOT frozen (cross-link field and category validation pend #2/#3); the Lane C router is BLOCKED; Trade Memory is EXCLUDED from all packets; the Base Constitution hard-gate amendment is a document milestone pending #4 (blocks the first merge into `integration`, not lane builds).

## RULES BINDING EVERY PACKET

1. Frozen contracts are read-only law. A build session that believes a contract is wrong records it in its lane NOTES.md and stops that thread — it never edits `contracts/`.
2. A session builds ONLY inside its Allowed Files. Touching another lane's directories is a failed gate, even if the change is correct.
3. If work cannot proceed without a HELD decision (#2, #3, #4, #14), the session stops that thread, records the blockage in NOTES.md, and continues other in-scope work. It never assumes the decision.
4. Sandbox config only (`config/sandbox.config.json`); the config loader must refuse production roots in sandbox mode, and no session ever creates a production config.
5. Branches in the Hold repository: `build/librarian-spine`, `build/manager-queue`, `build/receipt-ifta`, `build/reports`, merging one at a time into `integration` per blueprint 4.5, then `main`.
6. Every packet's session ends by writing/updating its lane NOTES.md: what was built, what was flagged, what was deliberately not built.

---

# PACKET A — LIBRARIAN EVIDENCE SPINE

**Mission.** Build the evidence spine of Dispatch — archive-on-registration, hashing, evidence indexing, retrieval — plus the shared plumbing (config, IDs, hashing, database bootstrap, audit writer) every other lane will use. This is the floor the system stands on; it merges first.

**Scope.**
- BUILDABLE NOW (everything — Lane A touches no held item): config loader with sandbox refusal; ULID generator; SHA-256 utilities; SQLite bootstrap (WAL, foreign keys, delete-revoking triggers on `evidence_records` and `audit_log`); audit writer per contract 1.6; the three-call evidence interface per contract 1.4 (`register` / `retrieve` / `link_children` — no update, no delete, permanently); Library evidence index; `tools/init_roots.py`, `tools/seed_library.py`, `tools/export_audit_rolls.py`; full Lane A test suite.
- BLOCKED / EXCLUDED: truth promotion, retrieval governance, Library metadata beyond the evidence index (later lane); anything touching FuelRecord/ExpenseRecord tables (held schemas — the bootstrap creates only tables whose schemas are in force: evidence, mileage, queue, audit).

**Dependencies.** Contracts 1.1, 1.4, 1.6; approved doctrines #1, #5, #6, #10. No lane dependencies. No stubs consumed.

**Allowed Files.** `src/dispatch/common/**` · `src/dispatch/evidence/**` · `tools/init_roots.py`, `tools/seed_library.py`, `tools/export_audit_rolls.py` · `tests/lane_a/**` · `tests/conformance/**` (Lane A creates the shared conformance suite from `contracts/`) · `docs/lanes/A/NOTES.md`.

**Forbidden Files.** `contracts/**` (read-only) · `config/dispatch.config.json` (production — must not exist yet) · `src/dispatch/{queue,receipt,ifta,reports}/**` · `library_seed/Constitutions/**` (doctrine content is Mike's) · any path outside the Hold repository.

**Validation Gates.** (1) Conformance suite green against contracts 1.4/1.6 and the in-force schemas. (2) Golden regression: immutability, hash round-trip, register→retrieve fidelity, duplicate-hash returns existing record flagged `duplicate_document`, retention class defaulting, audit-entry-per-operation. (3) Boundary refusal: modify-after-archive fails; no update/delete code path exists on archived files, `evidence_records`, or `audit_log` (verified by test AND by grep of the module surface); sandbox-mode production-root refusal fires. (4) Audit completeness sampled. (5) Mike's walkthrough: register a real document in sandbox, retrieve it, verify the hash. (6) NOTES.md complete; docs match as-built.

**Expected Deliverables.** Working `dispatch.common` and `dispatch.evidence` packages; the three tools; the shared conformance suite; Lane A tests green; README for the three interface calls; NOTES.md; branch `build/librarian-spine` ready for `integration`.

**Claude Sonnet Build Prompt.**
```
You are building LANE A of Dispatch Matrix Group 1 in the Hold repository,
branch build/librarian-spine. You are a bounded build session.

APPROVAL CONTEXT (2026-08-03): items #2 (dual-record fuel), #3 (expense
vocabulary), #4 (hard gates), #14 (Trade Memory) are ON HOLD. Lane A touches
none of them. If any thread of work seems to need one, STOP that thread and
record it in docs/lanes/A/NOTES.md.

READ FIRST: DISPATCH_BUILD_BLUEPRINT_v1 Parts 1.1, 1.4, 1.6, 3, 4.1, 5;
contracts/evidence_record.schema.json, mileage_record.schema.json,
queue_item.schema.json, audit_entry.schema.json, config.schema.json;
the approved failure and deletion doctrines.

BUILD: src/dispatch/common/ — config loader (validates config; REFUSES to run
if environment=sandbox and any root resolves under a production D:\ path),
ULID, SHA-256 utils, SQLite bootstrap (WAL, FKs, delete-revoking triggers on
evidence_records and audit_log; create ONLY tables whose schemas are in force:
evidence_records, mileage_records, queue_items, audit_log — do NOT create
fuel_records or expense_records tables; their schemas are held), audit writer
(INSERT-only) per contract 1.6.
src/dispatch/evidence/ — register/retrieve/link_children exactly per contract
1.4: register archives the original under ARCHIVE\Evidence\YYYY\MM\ BEFORE any
other processing, sets read-only, hashes, dedups by hash (duplicate ⇒ return
existing record flagged duplicate_document), writes the Library index entry;
retrieve verifies hash and raises + enqueues an exception queue item on
mismatch; link_children appends derived ids. There is NO update and NO delete
in this interface, permanently.
tools/init_roots.py, seed_library.py, export_audit_rolls.py.
tests/conformance/ generated from contracts/ (this suite is shared property —
build it clean), tests/lane_a/ per blueprint Part 5.

MUST NOT: edit contracts/; create production config; touch
src/dispatch/{queue,receipt,ifta,reports}; write any update/delete path for
archived data; hardcode any filesystem root; make network calls; expand scope
(flag ideas in NOTES.md instead).

DONE WHEN: all Lane A + conformance tests green including the negative tests
(modify-after-archive FAILS, sandbox refusal FIRES); every operation audited;
README and docs/lanes/A/NOTES.md written; branch ready for integration.
```

---

# PACKET B — MANAGER WORK QUEUE

**Mission.** Build the single escalation channel of Dispatch: the decision/review queue and its human interface. Every approval, exception, and quarantine in the system terminates here. Its constitutional behaviors — silence is never consent, the full queue is always visible, nothing is ever silently discarded — are features to be tested as hard as the mechanics.

**Scope.**
- BUILDABLE NOW (all mechanics — fully specified by approved items): queue store per contract 1.3; transitions (`open→in_review→approved/rejected/resolved`) each writing an audit entry; priority triage (`urgent`/`today`/`whenever`); Flask queue UI — priority-grouped list, item detail with evidence preview via the Lane A interface (stub until A merges), approve/reject/resolve with required `decided_by` and optional note; tablet-friendly layout; retention of decided items.
- BLOCKED / EXCLUDED: nothing mechanical. NOTE on #4: the enumerated hard-gate LIST is held, but the queue's mechanics are gate-agnostic — it processes whatever items workers submit. No queue code depends on #4. The only #4 consequence is repository-level: the first merge into `integration` waits for the Base Constitution amendment (docs-match-as-built gate).

**Dependencies.** Contract 1.3, 1.6; approved #5, #7. Consumes Lane A's audit writer and evidence retrieve — via vendored stubs with identical signatures until Lane A merges, then swapped.

**Allowed Files.** `src/dispatch/queue/**` (including its Flask templates/static) · `tests/lane_b/**` · `tests/stubs/audit_stub.py`, `tests/stubs/evidence_stub.py` (kept deliberately dumb) · `docs/lanes/B/NOTES.md`.

**Forbidden Files.** `contracts/**` · `src/dispatch/common/**` and `src/dispatch/evidence/**` (Lane A property — use the stubs, never edit the real thing) · `src/dispatch/{receipt,ifta,reports}/**` · production config · anything outside the Hold repository.

**Validation Gates.** (1) Conformance vs contract 1.3. (2) Golden regression: full lifecycle; audit entry per transition; decided items retained with notes. (3) Boundary refusal: NO code path and NO configuration flag can transition an item on a timer, scheduler, or default — write the negative test that proves auto-approval is impossible, not merely disabled; filtered views alter nothing; delete of a queue item is impossible. (4) Audit completeness sampled. (5) Mike's walkthrough: approve one item and reject one item from a tablet in sandbox. (6) NOTES.md complete; docs match as-built.

**Expected Deliverables.** Working `dispatch.queue` package + UI; stubs; Lane B tests green; NOTES.md; branch `build/manager-queue` ready for `integration` (its merge follows Lane A's).

**Claude Sonnet Build Prompt.**
```
You are building LANE B of Dispatch Matrix Group 1 in the Hold repository,
branch build/manager-queue. You are a bounded build session.

APPROVAL CONTEXT (2026-08-03): #2/#3/#4/#14 are ON HOLD. Lane B's mechanics
depend on none of them — the queue is gate-agnostic and processes whatever
items workers submit. If a thread seems to need a held decision, STOP it and
record in docs/lanes/B/NOTES.md.

READ FIRST: DISPATCH_BUILD_BLUEPRINT_v1 Parts 1.3, 1.6, 3, 4.2, 5;
contracts/queue_item.schema.json, audit_entry.schema.json; the approved
Manager boundary clause and failure doctrine.

BUILD: src/dispatch/queue/ — store per contract 1.3; transitions
open→in_review→approved/rejected/resolved, each writing an audit entry via the
audit interface (vendored stub tests/stubs/audit_stub.py with the real
signature until Lane A merges); priority triage urgent/today/whenever.
Flask UI: list grouped by priority; item detail with subject, payload refs,
evidence preview via the evidence retrieve interface (tests/stubs/
evidence_stub.py until Lane A merges — keep both stubs dumb); approve/reject/
resolve requiring decided_by, supporting decision_note. Big touch targets,
tablet-friendly, no crowding.

CONSTITUTIONAL BEHAVIORS — test as hard as features:
- No transition ever fires on a timer, scheduler, or default. There must be
  no code path and no config flag capable of auto-approval. Prove it with a
  negative test.
- The full queue is always visible; filters are views, never deletions.
- Rejected/resolved items are retained with notes, permanently. No delete.

MUST NOT: edit contracts/, common/, or evidence/ (stub, never edit); execute
domain work or call external systems from the queue; add notifications beyond
the UI (flag in NOTES.md); expand scope.

DONE WHEN: lifecycle, no-timer, visibility, retention, and audit tests green;
conformance green; a tablet walkthrough works in sandbox; docs/lanes/B/
NOTES.md written; branch ready (merges AFTER Lane A).
```

---

# PACKET C — RECEIPT → IFTA CHAIN (partially blocked; largest buildable core)

**Mission.** Build the Receipt Agent's intake-and-extraction pipeline and the IFTA Agent's preparation engine — everything on the diesel path that the current approval status permits — while cleanly parking the routing stage behind held decisions #2 and #3.

**Scope.**
- BUILDABLE NOW: intake watcher on `Intake\Drop` with evidence registration FIRST (evidence stub until Lane A merges; registration failure ⇒ `Intake\Quarantine` + exception queue item); parser registry — CSV (deterministic), ONE fuel-card statement format (parameterized), LLM-vision extraction for scans; deterministic validators — JSON structural check, sum validation (lines + tax = total, else exception), transaction dedup (key per contract 1.2; collision ⇒ suppress + flag, never drop), confidence threshold ⇒ quarantine; the **classified-line stage**: extraction terminates in validated, classified line items held in a `pending_routing` state with full provenance — the router that turns them into Fuel/Expense Records is BLOCKED; mileage intake `tools/mileage_worksheet.py` writing MileageRecords (schema in force); IFTA worksheet engine per blueprint 3.5 built against the in-force FuelRecord draft fields it needs (jurisdiction, gallons_normalized, tractor_or_reefer, purchase_date, evidence link) using golden-fixture fuel data — clearly marked provisional pending #2 freeze; all eight IFTA exception detectors; quarterly package builder with DRAFT status and seal-on-approval flow wired to the queue interface (stub until B merges).
- BLOCKED (await #2 dual-record fuel + #3 vocabulary): the router; FuelRecord/ExpenseRecord table creation and final schema freeze; category validation against the closed vocabulary; ExpenseRecord emission and the Accounting Queue staging; the `pending_routing → records` conversion. On approval of #2/#3, a Phase 2 packet (C-2) is issued — see Hold Re-Entry Protocol.
- EXCLUDED (await #14): the entire Trade Memory component — no pattern storage, no pattern reliance. Every unknown format goes to the review queue; human rulings accumulate in the audit trail and can seed patterns later.

**Dependencies.** Contracts 1.1, 1.2 (EvidenceRecord + MileageRecord in force; Fuel/Expense draft-only), 1.3, 1.4, 1.6; spec 3.5; approved #5, #12, #13. Stubs: evidence (until A merges), queue (until B merges). Golden assets: `tests/golden/receipts/` (Mike blesses expected outputs) and `tests/golden/ifta/` (one hand-computed quarter).

**Allowed Files.** `src/dispatch/receipt/**` · `src/dispatch/ifta/**` · `tools/mileage_worksheet.py` · `tests/lane_c/**` · `tests/golden/receipts/**`, `tests/golden/ifta/**` (fixtures + expected outputs; blessing is Mike's) · `tests/stubs/evidence_stub.py`, `tests/stubs/queue_stub.py` · `docs/lanes/C/NOTES.md`.

**Forbidden Files.** `contracts/**` · `src/dispatch/{common,evidence,queue,reports}/**` · production config · any code creating `fuel_records`/`expense_records` tables or records (held) · any Trade Memory storage or logic (held) · any QuickBooks or external API call · anything outside the Hold repository.

**Validation Gates.** (1) Conformance vs in-force contracts (Evidence, Mileage, queue items it emits). (2) Golden regression: golden receipt set extractions match blessed JSON **to the classified-line stage**; hand-computed quarter reproduced exactly from fixture fuel data + entered mileage; all eight exception types fire from seeded data; dedup catches the receipt-vs-statement double; sum-validation catches seeded mismatches. (3) Boundary refusal: no GL codes anywhere; no vocabulary list embedded in code; IFTA cannot mutate a source record (read-only views + negative test); no auto-resolution of exceptions; no file/submit/transmit capability exists; `pending_routing` items cannot silently expire. (4) Audit completeness including quarantine flows. (5) Mike's walkthrough: drop one week of real receipts in sandbox; verify registration, extraction, quarantine behavior, and an IFTA draft worksheet from fixture+manual data. (6) NOTES.md separates built / blocked-parked / flagged.

**Expected Deliverables.** Working intake→extraction→validation→`pending_routing` pipeline; quarantine + exception flows; mileage worksheet tool; provisional IFTA engine + exceptions + draft package flow; golden suites wired; NOTES.md with an explicit BLOCKED section; branch `build/receipt-ifta` (merges after A and B; its own merge may itself wait on #2/#3 if they remain undecided — that is expected and correct).

**Claude Sonnet Build Prompt.**
```
You are building LANE C of Dispatch Matrix Group 1 in the Hold repository,
branch build/receipt-ifta. You are a bounded build session working under an
explicit PARTIAL HOLD.

APPROVAL CONTEXT (2026-08-03): #2 dual-record fuel and #3 expense vocabulary
are ON HOLD ⇒ you MUST NOT build the router, create fuel_records/
expense_records tables, emit those records, or validate categories. #14 Trade
Memory is ON HOLD ⇒ you MUST NOT build any pattern storage or reliance.
Extraction terminates at validated, classified line items in a pending_routing
state with full provenance. This is by design, not a gap. If you are tempted
to "just assume" a held decision, STOP and write it in docs/lanes/C/NOTES.md.

READ FIRST: DISPATCH_BUILD_BLUEPRINT_v1 Parts 1 (all), 3.5, 4.3, 5; the
approved Receipt (#12) and IFTA (#13) boundary clauses; the failure doctrine;
DISPATCH_RECEIPT_WORKFLOW_AUDIT_v1 Section 6 (routing table — context only;
the router itself is out of scope).

BUILD — RECEIPT (src/dispatch/receipt/): intake watcher on OPERATIONS\Intake\
Drop; EVERY document registers through the evidence interface FIRST
(tests/stubs/evidence_stub.py until Lane A merges; keep it dumb); registration
failure ⇒ Quarantine + exception queue item (queue stub until Lane B merges).
Parser registry: CSV (deterministic); one fuel-card statement format
(parameterized vendor profile, no guessing); LLM-vision extraction for scans.
EVERY path, including LLM output, passes deterministic validators: structural
check, sum validation (lines+tax=total else exception), dedup (contract 1.2
key; collision ⇒ suppress+flag, never silently drop), confidence threshold
(below ⇒ line-level quarantine; rest of document proceeds). Terminate in
pending_routing: classified line items + provenance, awaiting the future
router. No Trade Memory: unknown formats ⇒ review queue, period.

BUILD — IFTA (src/dispatch/ifta/): tools/mileage_worksheet.py writing
MileageRecords (schema in force, source=manual_worksheet); worksheet engine
exactly per blueprint 3.5 against golden-fixture fuel data (mark the fuel
input adapter PROVISIONAL pending #2); rates ONLY from versioned rate_tables,
version recorded on the worksheet; all eight exception detectors ⇒ queue;
quarterly package DRAFT + seal-on-approval flow via the queue interface.

MUST NOT: build the router; create or write fuel_records/expense_records;
embed any category vocabulary; build Trade Memory; mutate any source record
(read-only views — write the negative test); auto-resolve exceptions; call
QuickBooks or any tax authority endpoint; edit contracts/ or other lanes'
code; expand scope.

DONE WHEN: golden receipt set matches blessed output to the classified-line
stage; the hand-computed golden quarter reproduces exactly; all eight
exceptions fire from seeded data; dedup catches the receipt-vs-statement
double; boundary negative tests green; audit completeness verified;
conformance green; docs/lanes/C/NOTES.md contains an explicit BLOCKED section
listing everything parked behind #2/#3/#14; branch ready.
```

---

# PACKET D — REPORTS LAYER

**Mission.** Build the deterministic answer surface of Dispatch — a layer, not an agent — over fixture data conforming to the in-force schemas: Fuel Spend and IFTA Position now, the shell ready for Expense Summary the day #3 lands. Reads governed storage; writes nothing but the print queue. For the person using it, this screen is Dispatch.

**Scope.**
- BUILDABLE NOW: template engine (report = versioned JSON template — query definition + layout — loaded from `LIBRARY\Templates\Reports\`; rendering = template version + as-of timestamp + data; identical inputs ⇒ identical output); Flask UI per the design review — Recents chips (last three runs), Report Type / six Date Range presets / context-sensitive Filter (Truck if fleet > 1, State on fuel/IFTA), no Sort By; big-number visual answers with comparison line, below-the-fold breakdown, freshness line + pending-review count; **Fuel Spend** (over fuel fixture data) and **IFTA Position** (reads STORED worksheet values only, labeled "Prepared — estimate, not filed," exception count inline); Save For Printing ⇒ immediate immutable HTML snapshot to `ARCHIVE\ReportSnapshots\YYYY\` (template version + as-of stamped) + print-queue REFERENCE; print stylesheet; read-only DB connection (`mode=ro`) everywhere except the single snapshot/print-queue writer.
- BLOCKED (await #3): the Expense Summary template, its Category filter, and its fixtures — the closed vocabulary defines both. Build the template engine so that adding Expense Summary later is a template file + fixture, zero code change.
- NOTE on #2: Fuel Spend fixtures use the in-force FuelRecord draft fields (date, jurisdiction, gallons_normalized, total_amount, unit_number); no fixture may presuppose or exclude the D1 cross-link. Mark the fixture README accordingly.

**Dependencies.** Contracts 1.1, 1.6, in-force schema fields; blueprint 4.4; DISPATCH_REPORTS_DESIGN_REVIEW_v1 Sections 2, 3, 5, 6. Fixture data only; final fidelity gate re-runs against real Lane C data on `integration` before merge 5.

**Allowed Files.** `src/dispatch/reports/**` (including templates/static) · `tests/lane_d/**` · `tests/fixtures/**` · report template JSON files under `library_seed/Templates/Reports/**` · `docs/lanes/D/NOTES.md`.

**Forbidden Files.** `contracts/**` · `src/dispatch/{common,evidence,queue,receipt,ifta}/**` · production config · any DB write path outside the snapshot/print-queue writer · any Expense Summary artifacts (held) · anything outside the Hold repository.

**Validation Gates.** (1) Conformance of fixtures vs in-force schemas. (2) Golden regression: determinism (identical inputs ⇒ identical bytes, repeated); fidelity (every displayed total equals independent SQL arithmetic on the same fixtures); IFTA display-only (values match the stored worksheet fixture exactly — never recomputed); snapshot-on-save with correct stamps; queue-clear never touches Archive copies. (3) Boundary refusal: any write outside the snapshot/print-queue writer fails (negative test on the ro connection); no tax math or rate table anywhere in the lane (verified by test and by grep); no report type renders without complete data behind it. (4) Audit entries for snapshot/save actions. (5) Mike's walkthrough: "fuel today" answered in one glance on a tablet over LAN in sandbox; save-for-print round trip. (6) NOTES.md complete; FINAL fidelity gate explicitly deferred to integration with real Lane C data — recorded as an open item, not skipped.

**Expected Deliverables.** Working `dispatch.reports` package + UI; Fuel Spend and IFTA Position templates (versioned, seeded to Library); fixtures + fixture README; print/snapshot flow; Lane D tests green; NOTES.md; branch `build/reports` (merges LAST).

**Claude Sonnet Build Prompt.**
```
You are building LANE D of Dispatch Matrix Group 1 in the Hold repository,
branch build/reports. You are a bounded build session. Reports is a LAYER,
not an agent: it reads governed storage and writes nothing but the print
queue. Its numbers must never be wrong — for the user, this screen IS Dispatch.

APPROVAL CONTEXT (2026-08-03): #3 expense vocabulary is ON HOLD ⇒ do NOT
build the Expense Summary template, Category filter, or expense fixtures.
Build the template engine so Expense Summary lands later as a template file +
fixture with ZERO code change. #2 is ON HOLD ⇒ fuel fixtures use in-force
draft fields only and must not presuppose or exclude the D1 cross-link (say
so in the fixture README). If a thread needs a held decision, STOP and record
it in docs/lanes/D/NOTES.md.

READ FIRST: DISPATCH_BUILD_BLUEPRINT_v1 Parts 1, 3, 4.4, 5;
DISPATCH_REPORTS_DESIGN_REVIEW_v1 Sections 2, 3, 5, 6.

BUILD (src/dispatch/reports/): template engine — a report is a versioned JSON
template (query definition + layout) from LIBRARY\Templates\Reports\;
rendering = template version + as-of timestamp + data; identical inputs must
produce identical bytes. Flask UI: Recents chips (last three runs, one tap);
dropdowns Report Type / Date Range (Today, Yesterday, This Week, This Month,
Last Month, Custom) / context-sensitive Filter (Truck only if fleet>1, State
on fuel/IFTA) — NO Sort By. Visual answer: one big number readable at arm's
length, secondary figure beneath, one comparison line, breakdown below the
fold, freshness line with pending-review count. A chart is decoration under
the answer, never the answer. Reports: Fuel Spend (fuel fixtures) and IFTA
Position (reads STORED ifta_worksheets fixture values ONLY, labeled
"Prepared — estimate, not filed", exception count inline). Save For Printing:
immediate immutable HTML snapshot to ARCHIVE\ReportSnapshots\YYYY\ stamped
with template version + as-of; print_queue holds a REFERENCE; clearing the
queue never touches the Archive copy. Print stylesheet. DB opened READ-ONLY
(mode=ro) everywhere except the single snapshot/print-queue writer.

MUST NOT: any write outside that single writer (prove with a negative test);
any tax math, rate table, or recomputation of stored IFTA values; any report
type without complete data behind it; localStorage or client state that
changes numbers; PDF generation; editing contracts/ or other lanes' code;
scope expansion.

DONE WHEN: determinism test green (identical inputs ⇒ identical bytes,
repeated); fidelity test green (displayed totals = independent SQL arithmetic
on the same fixtures); IFTA display-only test green; read-only enforcement
test green; snapshot stamps verified; fast on a tablet over LAN in sandbox;
conformance green; docs/lanes/D/NOTES.md notes the deferred final fidelity
gate (re-run on integration against real Lane C data before merge 5); branch
ready (merges LAST).
```

---

# HOLD RE-ENTRY PROTOCOL

When a held item is decided, work resumes by issuing a small follow-on packet — never by informally widening an open lane's scope:

- **#2 + #3 approved →** issue **PACKET C-2 (Router & Freeze)**: freeze FuelRecord/ExpenseRecord v1.0 in `contracts/`; create their tables; build the router (D1 outcome as decided; category validation against the approved vocabulary file in Library); convert `pending_routing` items; extend the golden receipt set expectations from classified-line stage to full records; extend conformance. Also unlocks Lane D's Expense Summary (template + fixtures, no code change if Packet D was built right).
- **#4 approved →** document work only: adopt the Base Constitution amendment, stamp the version, and the first merge into `integration` is cleared (validation gate 6, docs-match-as-built).
- **#14 approved →** issue **PACKET C-3 (Trade Memory)** before any journeyman certification: pattern storage per the adopted doctrine, seeded from the human rulings already accumulated in the audit trail.
- A held item **rejected or amended** flows the same way: Mike's decision → contract/doctrine version bump → follow-on packet reflecting the decision. No open session ever absorbs a decision mid-build; sessions end, packets begin.

# EXECUTION ORDER SUMMARY

Start now, in parallel: **A** (leads), **B**, **C** (buildable core), **D** (fixtures). Merge strictly: A → B → C (may pause for #2/#3) → C-2 (when unlocked) → D → later: Truth Governance, C-3. First merge into `integration` additionally waits on #4 (document milestone). All work in the Hold repository, sandbox roots only, until Mike cuts over after merge 5.

*End of DISPATCH_MATRIX_EXECUTION_PACKAGE_v1. Contains no implementation code. Nothing here overrides DISPATCH_BASE_CONSTITUTION_v1 or proceeds past a hold.*

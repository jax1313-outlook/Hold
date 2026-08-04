# DISPATCH_BUILD_BLUEPRINT_v1

Purpose: the complete, build-ready blueprint for Dispatch Workforce Core v1 — Matrix Group 1.
Derived from: seven pre-coding audits (architecture, boundaries, memory, receipt workflow, Reports, build matrix, final review).
Stack: Python 3.11+ · SQLite · Flask (Reports UI) · local-first on Windows against the D:\ roots.
Authority: Mike Zachary is final authority. Items marked **[MIKE APPROVES]** are drafted for his sign-off, not yet law.

---

# PART 0 — HOW TO USE THIS BLUEPRINT

Order of operations:

1. Mike reviews and approves Part 1 (Contract Pack) and Part 2 (constitution amendments). Every **[MIKE APPROVES]** item gets a yes/no/edit. When approved, stamp each contract `v1 FROZEN` with the date.
2. Create the repository and directory skeleton (Part 3).
3. Launch build lanes using the coding prompts in Appendices A–D. Lane A starts first; B and C may start the same day; D starts once fixtures exist.
4. Merge strictly in order (Part 4.5), each lane through the six validation gates (Part 5).
5. Publisher, Intelligence, Accounting, and the QuickBooks connector are NOT in this blueprint. Their tripwires are recorded in the final review; no prompts exist for them by design.

Rule that governs everything below: **a frozen contract changes only by Mike's decision, a version bump, and same-day notice to every open lane.**

---

# PART 1 — CONTRACT PACK v1

## 1.1 Storage mapping and configuration

The word "Memory" is retired as a tier name. Three logical tiers, three physical roots:

| Logical tier | Meaning | Physical root |
|---|---|---|
| OPERATIONS | living system — open-period records, queues, trade memory, print queue, intake | `D:\Dispatch Operations` |
| LIBRARY | approved truth — constitutions, templates, procedures, vocabulary, rate tables, evidence index | `D:\Memory\Library` |
| ARCHIVE | history — immutable originals, sealed bundles, report snapshots, audit rolls | `D:\Archive` |

Trade Memory is per-worker working knowledge and lives under OPERATIONS (`Workers\<name>\TradeMemory\`), inspectable, never secret.

**All paths come from one config file. No component ever hardcodes a root.**

`dispatch.config.json` (schema):
```
{
  "environment": "production" | "sandbox",
  "roots": {
    "operations": "D:\\Dispatch Operations",
    "library":    "D:\\Memory\\Library",
    "archive":    "D:\\Archive"
  },
  "database": "<operations>\\Data\\dispatch.db",
  "schema_versions": { "fuel_record": "1.0", "expense_record": "1.0",
                       "evidence_record": "1.0", "mileage_record": "1.0",
                       "queue_item": "1.0", "audit_entry": "1.0" }
}
```
Sandbox config points every root at test directories (e.g. `D:\DispatchSandbox\...`). A component MUST refuse to start if `environment` is `sandbox` but any root resolves under a production path. **[MIKE APPROVES the mapping]**

## 1.2 Record schemas

### Decision D1 — dual-record fuel: ADOPTED **[MIKE APPROVES]**
A propulsion-fuel line item emits BOTH a Fuel Record (→ IFTA) and an Expense Record, category `fuel` (→ Accounting Queue), cross-linked, sharing one Evidence Record parent. Reefer-flagged fuel emits an Expense Record only (category `reefer_fuel`). DEF is never a Fuel Record.

### FuelRecord v1.0
| Field | Type | Req | Notes |
|---|---|---|---|
| fuel_record_id | TEXT (ULID) | ✔ | primary key |
| evidence_record_id | TEXT | ✔ | provenance parent |
| expense_record_id | TEXT | ✔ | D1 cross-link |
| purchase_date | DATE | ✔ | business date |
| purchase_time | TIME | – | when present |
| vendor_name | TEXT | ✔ | IFTA: seller name |
| vendor_address | TEXT | ✔ | IFTA: seller address |
| jurisdiction | TEXT(2) | ✔ | state/province code, derived from address, never guessed |
| fuel_type | TEXT | ✔ | `diesel` \| `gasoline` |
| tractor_or_reefer | TEXT | ✔ | `tractor` \| `reefer` (reefer ⇒ excluded from IFTA gallons) |
| volume_as_received | REAL + unit | ✔ | gallons or liters as printed |
| gallons_normalized | REAL | ✔ | liters × 0.264172 when needed |
| unit_price / total_amount / currency | REAL/REAL/TEXT | ✔ | USD or CAD |
| taxes_included | BOOL | ✔ | pump vs bulk handling |
| unit_number | TEXT | ✔ | truck |
| driver | TEXT | – | |
| odometer | INTEGER | – | strengthens MPG check |
| payment_method / card_last4 | TEXT | – | dedup component |
| receipt_number | TEXT | – | dedup component |
| dedup_key | TEXT | ✔ | sha256(vendor_name + purchase_date + total_amount + gallons_normalized + card_last4) |
| extraction_confidence | REAL 0–1 | ✔ | below threshold ⇒ review queue |
| review_status | TEXT | ✔ | `auto` \| `human_confirmed` \| `quarantined` |
| schema_version | TEXT | ✔ | "1.0" |

### ExpenseRecord v1.0
expense_record_id (ULID) · evidence_record_id ✔ · fuel_record_id (when D1 twin) · purchase_date ✔ · vendor_name ✔ · vendor_location · line_description ✔ (verbatim) · **category ✔ (closed vocabulary 1.5 — validation rejects anything else)** · amount ✔ · tax_amount · currency ✔ · payment_method / card_last4 · unit_number · driver · load_id · dedup_key ✔ · status ✔ (`staged` | `approved` | `posted`) · quickbooks_ref · extraction_confidence ✔ · review_status ✔ · schema_version ✔.
Forbidden fields (never added): GL account code, deductibility, tax treatment, reimbursement status.

### EvidenceRecord v1.0
evidence_record_id (ULID) · archive_path ✔ (under ARCHIVE root) · file_hash ✔ (SHA-256) · document_type ✔ (`pump_receipt` | `fuel_card_statement` | `credit_card_statement` | `invoice` | `csv_export` | `email_attachment`) · vendor · document_date ✔ · capture_date ✔ · statement_period_start/end (statements) · page_count · derived_record_ids ✔ (JSON array — the container's children) · extraction_status ✔ (`complete` | `partial` | `failed` | `duplicate_document`) · duplicate_of · reviewed_by / review_date · retention_class ✔ (default `ifta_4yr`) · schema_version ✔.

### MileageRecord v1.0
mileage_record_id (ULID) · unit_number ✔ · period_start ✔ · period_end ✔ · jurisdiction ✔ (2-char) · miles ✔ (REAL > 0) · source ✔ (`manual_worksheet` | `ops_agent` | `eld_import`) · odometer_start/end (optional) · entered_by ✔ · schema_version ✔.
v1 reality: `manual_worksheet` entered by Mike via a simple form; the schema is identical when Dispatch Ops automates it later — the contract stays honest.

## 1.3 Queue item contract v1.0
queue_item_id (ULID) · type ✔ (`approval` | `review` | `exception` | `decision`) · source_worker ✔ · created_at ✔ · priority ✔ (`urgent` | `today` | `whenever` — triage labels authored by Mike) · subject ✔ (one line, human-readable) · payload_refs (JSON: record/evidence ids) · status ✔ (`open` | `in_review` | `approved` | `rejected` | `resolved`) · decided_by / decided_at / decision_note.
Constitutional rules enforced in code: **no status transition ever fires on a timer** (silence is never consent); the full queue is always visible; every transition writes an audit entry; rejected/quarantined items are never deleted, only resolved with a note.

## 1.4 Archive / evidence interface v1.0
Three operations, exposed as a Python module (`dispatch.evidence`):
- `register(file_path, document_type, metadata) -> EvidenceRecord` — copies the original into `ARCHIVE\Evidence\YYYY\MM\<evidence_id>.<ext>`, computes SHA-256, sets the file read-only, inserts the EvidenceRecord, writes the Library index entry, returns the record. Registration happens BEFORE any extraction. Duplicate hash ⇒ returns existing record flagged `duplicate_document`.
- `retrieve(evidence_record_id) -> (record, verified_path)` — verifies hash on read; mismatch raises and queues an `exception`.
- `link_children(evidence_record_id, derived_record_ids)` — appends to the container's child list.
There is no `update` and no `delete` in this interface, permanently. (Stub for Lane C: same three signatures over a temp directory + SQLite table — kept deliberately dumb.)

## 1.5 Closed expense vocabulary v1 **[MIKE APPROVES — he may add/remove before freeze]**
`fuel` · `reefer_fuel` · `def` · `meals` · `oil_additives` · `parts_maintenance` · `truck_wash` · `parking` · `tolls` · `scale_tickets` · `permits_fees` · `supplies` · `misc`.
No worker may extend this list. An unclassifiable line quarantines to the review queue; the rest of the document routes normally.

## 1.6 Audit entry format v1.0
Append-only SQLite table `audit_log` (INSERT-only; no UPDATE/DELETE statements exist in the codebase), exported monthly to `ARCHIVE\AuditRolls\YYYY-MM.jsonl`:
`ts · actor ✔ (worker name or "human:mike") · actor_version · constitution_version · action ✔ · input_refs (JSON) · output_refs (JSON) · gate_ref (when a hard gate was crossed: who approved, queue_item_id) · trade_memory_refs (patterns relied on — this is what makes learned behavior auditable) · outcome ✔ (completed | flagged | quarantined) · note`.

---

# PART 2 — CONSTITUTION AMENDMENTS (drafted language, ready for adoption)

## 2.1 DISPATCH_BASE_CONSTITUTION_v1 — additions **[MIKE APPROVES]**

**HARD APPROVAL GATES (no worker constitution may weaken these):**
1. No government filing or submission of any kind without explicit human approval.
2. No write to any accounting system (QuickBooks or successor) without explicit human approval.
3. No externally binding communication — rate acceptance, load booking or cancellation, contract terms, signatures, or any "accept" action — without explicit human approval. Informational communication (status, ETA, check calls, transmission of already-approved documents) is not gated.
4. No demotion, deletion, or in-place modification of promoted truth in the Library. Change is by supersession only, through the Librarian, with human approval.
5. No amendment to any constitution except by Mike Zachary, with a version increment.
6. No creation, modification, or retirement of any worker or helper layer except by Mike Zachary.
7. Approval is an affirmative act recorded in the decision queue. Silence, timeout, or absence is never consent.

**FAILURE DOCTRINE:** On any failure, ambiguity, or boundary conflict, a worker stops the affected work item, quarantines it unchanged, posts it to the Manager's decision queue with reason and evidence references, and continues unaffected work. No worker may silently skip, guess, discard, or retry-past a failing item. No worker may modify source data to make its own output balance.

**DELETION & RETENTION:** No worker deletes anything, anywhere, ever. The Librarian archives. Only Mike destroys, and never inside a statutory retention window (IFTA evidence: 4 years minimum; default class on all financial evidence).

## 2.2 Worker boundary clauses (from the boundary audit — insert verbatim into each worker constitution) **[MIKE APPROVES]**
1. **Manager:** routes work, tracks approvals, and protects attention; it does not approve, execute domain work, own external integrations, or commission workers; filtered items are deferred and logged, never discarded, and the full queue is always visible to Mike.
2. **Intelligence:** delivers analysis and recommendations to the Manager's decision queue only; no recommendation is a work order; bid/no-bid is always a human decision.
3. **Publisher:** manages production and conformance editing of assets it did not originate; obtains all inputs through the Librarian; its approval routing always terminates at a human.
4. **Librarian:** applies promotion, retention, and access rules issued by Mike; enforces policy, proposes policy, never authors policy in force; sole writer to Library and Archive; custodian of the Archive.
5. **Dispatch Ops:** performs informational external communication freely; any communication that binds Level 1 Transport requires human approval before transmission (Base gate 3).
6. **Receipt Agent:** extracts and classifies into Fuel, Expense, and Evidence Records with transaction-level duplicate detection; assigns no GL codes, performs no reconciliation, renders no accounting judgment; its classification vocabulary is closed (Contract 1.5).
7. **IFTA Agent:** prepares worksheets, exceptions, and packages from supplied fuel and mileage records; never adjusts source data, never corresponds with a tax authority, never files or pays.

## 2.3 Trade Memory rules (into the memory doctrine) **[MIKE APPROVES]**
Trade Memory lives at `OPERATIONS\Workers\<name>\TradeMemory\` as human-readable JSON; inspectable by Mike and the audit trail at all times. Entry types are closed: `format_pattern` | `exception_pattern` | `efficiency_note` | `validated_shortcut`. Anything rule-shaped ("always route X to Y", "skip check when...") is rejected at write time and escalated as a proposal. Patterns are hypotheses: validated by human confirmation during apprenticeship, and a pattern that stops matching flags — it never force-fits. Trade Memory may optimize HOW a worker checks, never WHETHER it checks. **At journeyman certification, Trade Memory is snapshotted and becomes read-only; post-freeze lessons queue as proposals for human-approved incorporation followed by re-certification against the regression suite.** Promotion path: worker proposes → Librarian routes → Mike approves → enters Library as company knowledge.

---

# PART 3 — SYSTEM ARCHITECTURE

## 3.1 Stack and rationale
- **Python 3.11+** — every worker, the pipeline, and all tooling. One language, one venv, easiest for AI build sessions to produce reliably.
- **SQLite** (`OPERATIONS\Data\dispatch.db`, WAL mode) — records, queues, audit log, worksheets. Single-writer local reality fits SQLite perfectly; no server to run.
- **Flask + server-rendered HTML** — the Reports UI and the decision-queue UI, served on the LAN (`http://<workstation>:8484`), tablet-friendly. No JS framework; big numbers, big touch targets.
- **Extraction** — hybrid: deterministic parsers for structured inputs (CSV exports, known statement layouts) and an LLM-vision call (Claude API) for scanned/photographed receipts, ALWAYS followed by deterministic validation: schema check, vocabulary check, sum validation, dedup, confidence threshold. The model proposes; the validators dispose. The code defines HOW; the Constitution defines WHAT and WHY.
- **No cloud dependencies** for storage or state. The LLM call is the only network dependency, and extraction degrades to the review queue when offline.

## 3.2 Repository layout
```
dispatch/
  config/dispatch.config.json     (production)  + sandbox.config.json
  contracts/          JSON Schema files for every Part-1 contract (the frozen law, versioned)
  src/dispatch/
    common/           config loader, ULID, hashing, db, audit writer
    evidence/         Lane A: archive/evidence interface + Library index
    queue/            Lane B: decision/review queue + Flask queue UI
    receipt/          Lane C: intake, parsers, LLM extraction, validators, router
    ifta/             Lane C: worksheet engine, exceptions, package builder
    reports/          Lane D: template engine, Flask UI, print queue
  library_seed/       constitutions, templates, vocabulary, IFTA rate tables → installed to LIBRARY
  tests/
    conformance/      generated from contracts/ — runs in EVERY lane
    golden/receipts/  the golden set: originals + expected-output JSON
    golden/ifta/      one hand-computed quarter
  tools/              init_roots.py, seed_library.py, export_audit_rolls.py, mileage_worksheet.py
```
Branches: `main` (always releasable) ← `integration` (serialized merges) ← `build/librarian-spine`, `build/manager-queue`, `build/receipt-ifta`, `build/reports`.

## 3.3 SQLite tables
`evidence_records`, `fuel_records`, `expense_records`, `mileage_records`, `queue_items`, `audit_log` (INSERT-only), `ifta_worksheets`, `ifta_worksheet_lines`, `ifta_exceptions`, `rate_tables` (jurisdiction, quarter, fuel type, rate, source version), `report_templates` (id, version, file ref in LIBRARY), `print_queue` (references to archived snapshots). Every record table carries `schema_version`. Foreign keys ON; deletes revoked by trigger on `evidence_records`, `audit_log`, and all record tables (UPDATE allowed only on status/review fields via whitelisted views).

## 3.4 Directory skeleton (created by `tools/init_roots.py` from config)
```
OPERATIONS\  Data\  Intake\{Drop,Processing,Quarantine}\  PrintQueue\
             Workers\{Manager,Receipt,IFTA,Librarian}\TradeMemory\
             Testing\GoldenSet\
LIBRARY\     Constitutions\  Templates\Reports\  Vocabulary\  RateTables\  EvidenceIndex\
ARCHIVE\     Evidence\YYYY\MM\   IFTA\<quarter>\   ReportSnapshots\YYYY\   AuditRolls\
```
Windows enforcement: archive files set read-only on write + SHA-256 verified on every read; code-level immutability (no update/delete paths exist) is the real fence, the attribute is the tripwire.

## 3.5 IFTA computation spec (for Lane C)
Per quarter, per fuel type: `fleet_mpg = total_miles_all_jurisdictions / total_tractor_gallons_normalized`. Per jurisdiction J: `taxable_gallons_J = miles_J / fleet_mpg`; `net_tax_J = taxable_gallons_J × rate_J − tax_paid_gallons_J × rate_J` (surcharge jurisdictions add the surcharge line from the rate table). Rates come ONLY from the versioned `rate_tables` for that quarter; the worksheet stores the rate-table version it used. Exceptions per the workflow audit: fuel-no-miles, miles-no-fuel-gap, MPG out of band (configurable, default 4.0–9.5), odometer discontinuity, broken evidence link, late documents from closed quarters, reefer contamination, rate-version mismatch. Worksheet is DRAFT until a human approves it through the queue; approval seals the bundle (worksheet + records + evidence refs) to `ARCHIVE\IFTA\<quarter>\`.

---

# PART 4 — BUILD MATRIX

## 4.1 Lane A — Librarian Evidence Spine (leads)
Builds: `src/dispatch/common/` (config, ULID, hashing, db bootstrap, audit writer — shared plumbing, built ONCE, here) and `src/dispatch/evidence/` (the 1.4 interface, Library evidence index, `tools/init_roots.py`, `tools/seed_library.py`, `tools/export_audit_rolls.py`).
Does NOT build: truth promotion, retrieval governance, metadata beyond the evidence index (Truth Governance is a later lane, after the memory doctrine amendments are adopted).
Depends on: contracts only. Everyone else depends on it.

## 4.2 Lane B — Manager Work Queue
Builds: `src/dispatch/queue/` — queue store per contract 1.3, transitions with audit entries, Flask queue UI (list by priority, item detail with evidence preview via Lane A retrieve, approve/reject/resolve with note), triage labels.
Constitutional behaviors tested from day one: no timer transitions anywhere; full-queue visibility; rejected items resolved-with-note, never deleted.
Depends on: common plumbing (from A; until A merges, vendored stub of the audit writer with identical signature).

## 4.3 Lane C — Receipt → IFTA chain (highest value)
Builds: `src/dispatch/receipt/` — intake watcher on `Intake\Drop`, evidence registration FIRST (via 1.4 — stub until A merges), parser registry (one fuel-card statement format + CSV), LLM-vision extraction wrapped in validators (schema, vocabulary, sum validation, dedup, confidence ≥ threshold else quarantine), router implementing the routing table (D1 dual-record fuel, DEF→expense only, reefer flag), quarantine flow to the review queue (primitive inbox until B merges).
And `src/dispatch/ifta/` — mileage intake (`tools/mileage_worksheet.py` manual-entry form in v1), worksheet engine per 3.5, exception detectors, quarterly package builder, seal-on-approval.
Depends on: frozen schemas; stubs for A and B; golden set for its gate.

## 4.4 Lane D — Reports (trails; safest)
Builds: `src/dispatch/reports/` — template engine (templates = JSON query definitions + layout, versioned in LIBRARY), Flask UI per the design review: Recents chips, Report Type (Fuel, Expenses, IFTA Position), six date presets, context-sensitive filters (Truck if fleet>1, State on fuel/IFTA, Category on expenses), big-number visual answers with freshness line and pending-review count, Save-For-Printing → HTML snapshot archived immediately (template version + as-of stamp) with print-queue reference; print stylesheet.
Bright lines in code: DB connection opened READ-ONLY (`mode=ro`) except a single print-queue writer; IFTA numbers read from `ifta_worksheets`, never recomputed.
Depends on: frozen schemas + fixture data; final fidelity gate needs Lane C's real output, hence merges last.

## 4.5 Merge order (strict, one at a time, each through all six gates)
1. Lane A (Evidence Spine) → 2. Lane B (Queue; C's inbox stub retires) → 3. Receipt Agent (archive stub retires) → 4. IFTA Agent → 5. Reports → 6. Librarian Truth Governance (later; gates Publisher, not Group 1).
After every merge event, all open lanes rebase from `integration`.

# PART 5 — VALIDATION GATES & TEST REQUIREMENTS

Six gates, every lane, before its merge:
1. **Contract conformance** — `tests/conformance/` (generated from `contracts/`) passes; shared fixtures byte-identical across lanes.
2. **Golden regression** — the lane's fixed test set passes: A: immutability/hash/dedup/round-trip suite · B: full lifecycle + no-timer + visibility suite · C-receipt: the golden receipt set (50 real docs, known-correct extractions — Mike blesses; grows but never shrinks) · C-ifta: the hand-computed quarter reproduced exactly + every exception type fired from seeded data · D: determinism (identical inputs ⇒ identical bytes) + fidelity (displayed totals = source arithmetic).
3. **Boundary refusal** — negative tests prove the fences: modify-after-archive fails; queue auto-approve config cannot exist; Receipt rejects any category outside 1.5; IFTA cannot mutate a source record (whitelisted-view enforcement test); Reports write attempt outside print queue fails.
4. **Audit completeness** — every action in the gate run produced a well-formed audit entry; sampled and verified.
5. **Human walkthrough** — Mike runs the lane end-to-end on real documents in the sandbox and signs off in writing. No merge on green checks alone.
6. **Docs match as-built** — worker constitution/context updated to what was actually built; divergences resolved in the documents first, because the documents are the law.

Cross-cutting rules: sandbox configs only until merge 5 completes and Mike cuts over; a failed merge backs out of `integration` cleanly; the golden sets and conformance suite run cumulatively on `integration` at every merge.

# PART 6 — WHAT THIS BLUEPRINT DELIBERATELY EXCLUDES
Publisher, Intelligence, Accounting Agent, QuickBooks live connector, credit card statement intake, monthly IFTA views, automated audit packages, reefer refund tracking, Compliance agent, Bid/Proposal seam, Dispatch Ops full build (first candidate for Matrix Group 2 — unblocks real mileage records, Cost Per Mile, and the Loads report). Each waits behind its named tripwire from the audit series. No coding prompts exist for them, by design.

---

# APPENDIX A — CODING PROMPT: LANE A (Librarian Evidence Spine)

```
MISSION
You are building Lane A of Dispatch Matrix Group 1: the Librarian Evidence Spine
and the shared plumbing every other lane will use.

You are a bounded build session. Do not exceed this scope.

READ FIRST (in this order)
1. DISPATCH_BUILD_BLUEPRINT_v1 — Parts 1, 3, 4.1, 5
2. contracts/ — evidence_record.schema.json, audit_entry.schema.json, config.schema.json
3. DISPATCH_BASE_CONSTITUTION_v1 — hard gates, failure doctrine, deletion doctrine

BUILD SCOPE
- src/dispatch/common/: config loader (validates dispatch.config.json; REFUSES to start
  if environment=sandbox and any root resolves under a production path), ULID generator,
  SHA-256 hashing, SQLite bootstrap (WAL, foreign keys, delete-revoking triggers on
  evidence_records and audit_log), audit writer (INSERT-only, per contract 1.6).
- src/dispatch/evidence/: register / retrieve / link_children exactly per contract 1.4.
  register() archives BEFORE any other processing, sets file read-only, dedups by hash
  (duplicate ⇒ return existing record flagged duplicate_document — never a second copy).
  retrieve() verifies hash on read; mismatch raises and enqueues an exception item
  (use the queue stub interface in tests/stubs/).
- tools/init_roots.py, tools/seed_library.py, tools/export_audit_rolls.py.
- Tests: the full Lane A suite in blueprint Part 5 gate 2, plus conformance tests.

BOUNDARIES — MUST NOT
- No update or delete code path on archived files, evidence_records, or audit_log. None.
- No truth promotion, retrieval governance, or Library metadata beyond the evidence index.
- No hardcoded paths anywhere; every path flows from the config loader.
- No network calls. No scope additions, even obvious ones — flag them in NOTES.md instead.

DEFINITION OF DONE
All Lane A tests green; conformance suite green; boundary-refusal tests green
(prove modify-after-archive FAILS); every operation writes a valid audit entry;
README documents the three interface calls; branch build/librarian-spine ready for
integration; NOTES.md lists anything you flagged but did not build.
```

# APPENDIX B — CODING PROMPT: LANE B (Manager Work Queue)

```
MISSION
You are building Lane B of Dispatch Matrix Group 1: the Manager's decision/review
queue and its human interface. The queue is the ONE escalation channel in Dispatch.

You are a bounded build session. Do not exceed this scope.

READ FIRST
1. DISPATCH_BUILD_BLUEPRINT_v1 — Parts 1.3, 1.6, 3, 4.2, 5
2. contracts/queue_item.schema.json, audit_entry.schema.json
3. DISPATCH_BASE_CONSTITUTION_v1 — gate 7 (silence is never consent), failure doctrine
4. Manager boundary clause (blueprint 2.2.1)

BUILD SCOPE
- src/dispatch/queue/: queue store per contract 1.3; transition functions
  (open→in_review→approved/rejected/resolved) each writing an audit entry;
  priority triage (urgent/today/whenever).
- Flask queue UI on the shared app: list view grouped by priority; item detail
  showing subject, payload refs, and evidence preview via the Lane A retrieve
  interface (stub until Lane A merges — tests/stubs/evidence_stub.py, keep it dumb);
  approve / reject / resolve actions requiring a decided_by identity and
  supporting a decision_note. Tablet-friendly: big targets, no crowding.

CONSTITUTIONAL BEHAVIORS (test these as hard as the features)
- NO transition ever fires on a timer, scheduler, or default. There must be no
  code path and no configuration flag that can auto-approve. Write the negative test.
- The full queue is always visible — no hidden or auto-discarded items; filtered
  views are views, never deletions.
- Rejected/resolved items are retained with their notes, permanently.

BOUNDARIES — MUST NOT
- The queue does not execute domain work, call external systems, or route data
  payloads — it holds decisions and references. No integrations. No notifications
  beyond the UI in v1 (flag ideas in NOTES.md).

DEFINITION OF DONE
Lifecycle suite green; no-timer negative test green; visibility test green;
audit-per-transition verified; conformance suite green; Mike can run an
approve-and-reject walkthrough in the sandbox from a tablet; branch
build/manager-queue ready; NOTES.md complete.
```

# APPENDIX C — CODING PROMPT: LANE C (Receipt → IFTA chain)

```
MISSION
You are building Lane C of Dispatch Matrix Group 1: the Receipt Agent (extraction
and routing clerk) and the IFTA Agent (quarterly preparation clerk). This is the
highest-value lane: a receipt in, a quarterly IFTA worksheet out, a human approving
instead of assembling.

You are a bounded build session. Do not exceed this scope.

READ FIRST
1. DISPATCH_BUILD_BLUEPRINT_v1 — Parts 1 (ALL contracts), 3.5, 4.3, 5
2. Receipt and IFTA boundary clauses (blueprint 2.2.6, 2.2.7); failure doctrine; hard gates
3. The routing table in DISPATCH_RECEIPT_WORKFLOW_AUDIT_v1 Section 6

BUILD SCOPE — RECEIPT (src/dispatch/receipt/)
- Intake watcher on OPERATIONS\Intake\Drop; every document goes to evidence
  registration FIRST (Lane A interface; stub until it merges), extraction second.
  Registration failure ⇒ document to Intake\Quarantine + exception queue item.
- Parser registry: (1) CSV exports — deterministic; (2) ONE fuel-card statement
  format (the card Level 1 actually runs — parameterize, don't guess the vendor);
  (3) scanned/photographed receipts via LLM-vision extraction (Claude API).
  EVERY path, including LLM output, passes deterministic validators: JSON-schema
  check, closed-vocabulary check (contract 1.5 — reject, never coerce), sum
  validation (lines + tax = total, else exception), dedup (key per contract 1.2 —
  collision ⇒ suppress + flag, never silently drop), confidence threshold
  (below ⇒ quarantine line to review queue; the rest of the document routes).
- Router: implements the routing table. Decision D1: propulsion fuel emits
  FuelRecord + ExpenseRecord(fuel), cross-linked. DEF is NEVER a FuelRecord.
  Reefer-flagged fuel: ExpenseRecord(reefer_fuel) only.
- Trade Memory: format patterns as JSON under Workers\Receipt\TradeMemory\ per
  blueprint 2.3 — closed entry types, human-confirmed before relied upon,
  pattern miss ⇒ flag, never force-fit. Every reliance is logged in the audit
  entry's trade_memory_refs.

BUILD SCOPE — IFTA (src/dispatch/ifta/)
- Mileage intake: tools/mileage_worksheet.py — a simple form writing
  MileageRecords (source=manual_worksheet) per contract 1.2.
- Worksheet engine exactly per blueprint 3.5; rates ONLY from versioned
  rate_tables; worksheet stores the rate-table version used.
- Exception detectors: all eight from blueprint 3.5. Exceptions go to the queue.
- Quarterly package builder; DRAFT until human approval through the queue;
  approval seals worksheet + records + evidence refs to ARCHIVE\IFTA\<quarter>\.

BOUNDARIES — MUST NOT
- Receipt: no GL codes, no reconciliation, no accounting judgment, no vocabulary
  extension, no QuickBooks calls (records go to status=staged, full stop).
- IFTA: never modify a fuel/mileage record (enforced via read-only views — write
  the negative test); never file, submit, transmit, or generate correspondence
  to any authority; never auto-resolve an exception.
- Neither worker deletes anything. Failures follow the failure doctrine:
  stop, quarantine, escalate — never skip, guess, or discard.

DEFINITION OF DONE
Golden receipt set green (extractions match blessed expected-output JSON);
hand-computed golden quarter reproduced exactly; every exception type fires from
seeded data; dedup catches the receipt-vs-statement double; D1 cross-links intact
on every fuel purchase; sum-validation catches seeded mismatches; boundary
negative tests green; audit completeness verified; conformance suite green;
Mike processes one real week of receipts end-to-end in the sandbox;
branch build/receipt-ifta ready; NOTES.md complete.
```

# APPENDIX D — CODING PROMPT: LANE D (Reports Layer)

```
MISSION
You are building Lane D of Dispatch Matrix Group 1: the Reports layer — a shared,
deterministic answer surface. It is a LAYER, not an agent. It reads governed
storage and writes nothing but the print queue. For the person using it, this
screen IS Dispatch — its numbers must never be wrong.

You are a bounded build session. Do not exceed this scope.

READ FIRST
1. DISPATCH_BUILD_BLUEPRINT_v1 — Parts 1, 3, 4.4, 5
2. DISPATCH_REPORTS_DESIGN_REVIEW_v1 — Sections 2, 3, 5, 6 (menu, reports, queue, storage)

BUILD SCOPE (src/dispatch/reports/)
- Template engine: a report = versioned JSON template (query definition + layout)
  loaded from LIBRARY\Templates\Reports\. Rendering = template version + as-of
  timestamp + data. Same inputs must produce identical output, always.
- v1 prebuilt reports: Fuel Spend, Expense Summary, IFTA Position.
  IFTA Position reads STORED worksheet values only, labeled
  "Prepared — estimate, not filed" with the open exception count inline.
- Flask UI per the design review: Recents chips (last three runs, one tap);
  dropdowns — Report Type, Date Range (Today/Yesterday/This Week/This Month/
  Last Month/Custom), context-sensitive Filter (Truck only if fleet>1, State on
  fuel/IFTA, Category on expenses); NO Sort By dropdown in v1.
  Visual answer: big number first (readable at arm's length), secondary figure
  beneath, one comparison line, breakdown below the fold, freshness line with
  pending-review count at the bottom. A chart is decoration under the answer,
  never the answer.
- Save For Printing: archives an HTML snapshot to ARCHIVE\ReportSnapshots\YYYY\
  IMMEDIATELY (immutable, stamped with template version + as-of), enqueues a
  REFERENCE in print_queue; print stylesheet for workstation printing; clearing
  the queue never touches the Archive copy.
- Build against fixtures conforming to the frozen schemas (tests/fixtures/).

BRIGHT LINES — MUST NOT (enforce in code, then test the enforcement)
- Database opened READ-ONLY (mode=ro) everywhere except one narrow print-queue/
  snapshot writer. Write the negative test proving any other write fails.
- Arithmetic yes (sum, average, count, group-by); domain judgment never:
  no tax math, no rate tables, no reclassification, no recomputing anything the
  IFTA Agent stored. If a number could differ from the owning agent's worksheet,
  it is a bug by definition.
- No report type ships without complete data behind it. No localStorage of state
  that changes numbers. No PDF generation in v1.

DEFINITION OF DONE
Determinism test green (identical inputs ⇒ identical bytes, repeated);
fidelity test green (every displayed total equals independent SQL arithmetic on
the same fixtures); IFTA display-only test green; read-only enforcement test
green; snapshot-on-save with stamps verified; loads fast on a tablet over LAN;
conformance suite green; FINAL GATE deferred by design: fidelity re-run against
real Lane C data on integration before merge 5; branch build/reports ready;
NOTES.md complete.
```

---

*End of DISPATCH_BUILD_BLUEPRINT_v1. Nothing in this document overrides DISPATCH_BASE_CONSTITUTION_v1. Frozen contracts change only by Mike's decision, a version bump, and same-day notice to every open lane.*

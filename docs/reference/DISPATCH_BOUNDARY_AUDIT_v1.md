# DISPATCH_BOUNDARY_AUDIT_v1

Auditor role: responsibility-boundary auditor
Scope: seven approved workers — job clarity, customers, boundaries, handoffs
Date: 2026-08-03
Authority: Advisory only. Mike Zachary is final authority.

Note: this round's worker summaries show that two round-1 defects were corrected — IFTA now consumes mileage records, and duplicate detection now has a named owner. Both fixes are acknowledged below; one of them (duplicate detection) is only half right.

---

## 1. WORKER-BY-WORKER RISK REVIEW

### Manager — CAN it become a super-agent? YES, through three doors.

**Door 1 — "bridges external systems."** Still in the summary, still the top structural risk in the architecture. Whoever holds the credentials and the integrations eventually holds the system. The Manager should route work and decisions; integrations belong to domain owners or a thin non-agent integration layer.
**Door 2 — "tracks approvals" sliding into granting approvals.** Tracking is clerical; granting is authority. Under time pressure, "Mike hasn't answered and it's routine" becomes auto-approval. The constitution must state: the Manager records and reminds; it never approves, and silence is never consent.
**Door 3 — attention protection becoming decision-making by omission.** A filter that decides what Mike never sees has decided the outcome. Control: filtered items are deferred and logged, never discarded; Mike can always view the full queue; triage rules (urgent / today / whenever) are written by Mike, not invented by the Manager.
**Verdict:** properly scoped as foreman only if the bridge role is removed and Doors 2–3 are closed in writing.

### Intelligence Agent — CAN it become the decision maker? YES, and the SAM expansion doubles the risk.

The generic vector: a recommendation phrased as an instruction, consumed by a worker that treats it as a work order. If Dispatch Ops ever acts directly on Intelligence output, Intelligence became the dispatcher.
The new vector: SAM, second pages, hidden requirements, special requirements — this is government solicitation analysis. "This opportunity fits us, bid it" is a business-development decision wearing a report costume. Bid/no-bid is Mike's call, always.
**Controls:** Intelligence output flows to exactly one customer — the Manager's decision queue — never directly to an executing worker. Every recommendation carries evidence, confidence, and at least one alternative (including "do nothing"). No worker's constitution may list Intelligence output as a valid work trigger.
**Verdict:** correctly scoped as analyst; needs its single-customer rule made explicit. Also note: the SAM workload is a future Bid/Proposal function incubating inside Intelligence (see Section 7).

### Publisher — CAN it become the creator of company truth? YES, via the edit-and-promote path.

The vector: Publisher "manages drafts" and "edits first pass," then "sends approved assets to Library." If the Librarian promotes on the Publisher's word, the Publisher has quietly become the author of record — its edits become truth without a human ever owning the claim.
A second, subtler vector: "identifies source repositories" and "gathers approved inputs" implies the Publisher roams storage directly. That collides with the Librarian's retrieval monopoly and lets the Publisher choose its own sources — choosing sources is choosing truth.
**Controls:** Publisher edits are conformance only (format, completeness, standards) and are tracked; the Publisher never originates a factual claim. "Approved" means human-approved — the Librarian promotes nothing that lacks a human approval mark. The Publisher requests inputs from the Librarian; it does not self-serve from repositories.
**Verdict:** correctly scoped as production manager only if retrieval goes through the Librarian and promotion requires human approval, not Publisher sign-off.

### Librarian — CAN it become policy authority? YES, if it authors its own promotion criteria.

The gatekeeper who writes the gate rules is the sovereign. A Truth Gatekeeper controls what every other worker retrieves — which means it controls what every other worker believes. If promotion criteria, retention rules, or metadata standards are invented by the Librarian rather than issued to it, the Librarian is legislating.
**Controls:** promotion criteria, retention rules, and the storage read/write matrix are written into the constitution by Mike; the Librarian applies them and proposes changes but never enacts changes. Retrieval is neutral — the Librarian returns what is asked for and flags staleness or conflict; it does not editorialize or withhold. Contested promotions and all demotions of promoted truth escalate to the decision queue.
**Verdict:** correctly scoped as clerk-of-record. The role is powerful by nature; the constitution must make it powerful and obedient rather than powerful and legislative.

### Dispatch Ops Agent — CAN it commit Level 1 Transport externally? YES — this is the highest-consequence boundary in the system.

The broker workflow is the exposure. Somewhere between "check call" and "accept the rate confirmation" is the line between reporting and contracting. Booking a load, accepting a rate con, agreeing to detention or accessorial terms, confirming capacity — each one binds the company's money, equipment, and legal position.
**Controls:** split broker communications into two enumerated classes. Informational (status updates, check calls, ETA notices, document transmission of already-approved items) — Ops may perform freely. Binding (rate acceptance, load booking/cancellation, term negotiation, anything with a signature or an "accept" button) — hard human approval gate, no exceptions, stated in the Base Constitution, not just the worker constitution. Ops may draft the acceptance; a human sends it.
**Verdict:** correctly scoped as execution worker only once the informational/binding line is written and enumerated. Until then this is the boundary most likely to produce a real-world incident.

### Receipt Agent — CAN it become Accounting? YES, by categorization creep.

The vector is a gradient with no natural stopping point: extract line items → classify record type → assign expense category → assign GL code → reconcile against statements → produce financial summaries. Each step seems like a small favor to the deferred Accounting function. Three steps in, the Receipt Agent is doing bookkeeping without a bookkeeping constitution.
**Controls:** the Receipt Agent's classification vocabulary is closed — Fuel Record, Expense Record, Evidence Record, plus field extraction, and nothing else. No GL codes, no deductibility judgments, no reconciliation, no aggregation, no financial statements. Anything requiring accounting judgment is flagged and queued, not decided.
**One correction to a round-1 fix:** duplicate detection moved to the Librarian, which is only half right. The Librarian can detect duplicate *documents* (same file, same scan). It cannot detect duplicate *transactions* — the same fuel purchase arriving once as a pump receipt and again as a line on the fuel-card statement. That is transaction-level dedup, it requires the extracted fields, and it belongs in the Receipt Agent at extraction time. Left unfixed, statements plus receipts double-produce Fuel Records and corrupt the IFTA return. Two dedup layers, two owners: transactions → Receipt Agent; documents → Librarian.
**Verdict:** correctly scoped as extraction clerk; needs the closed vocabulary rule and transaction-level dedup added.

### IFTA Agent — CAN it become tax filing authority? MOSTLY NO — "does not file or pay" is the right hard stop. Three residual leaks:

**Leak 1 — exception self-resolution.** If the IFTA Agent "fixes" a gallons/miles discrepancy to make the worksheet balance, it has made a tax judgment. Exceptions are flagged and queued; the agent never adjusts source data to reconcile.
**Leak 2 — audit support becoming audit response.** Preparing an audit package is clerk work; corresponding with a jurisdiction's auditor is representing the company before a tax authority. The IFTA Agent assembles; a human transmits and speaks.
**Leak 3 — rule interpretation.** Surcharge jurisdictions, split-rate quarters, exempt fuel — the agent applies published rate tables mechanically and flags anything requiring interpretation rather than resolving it.
**Verdict:** correctly scoped, best-bounded worker in the catalogue. Close the three leaks in its constitution and it is done.

---

## 2. RESPONSIBILITY OVERLAP TABLE

| # | Workers | Overlap | Resolution |
|---|---------|---------|------------|
| 1 | Manager ↔ all agents | "Bridges external systems" vs. domain-owned integrations | Remove bridge role from Manager; integrations live with domain owners or a non-agent integration layer |
| 2 | Manager ↔ Mike | "Tracks approvals" vs. granting approvals | Manager records, reminds, escalates; never approves; silence ≠ consent |
| 3 | Intelligence ↔ Manager/Mike | Recommendation vs. decision | Intelligence has one customer: the decision queue; no worker may execute on Intelligence output directly |
| 4 | Intelligence ↔ Publisher | SAM pipeline: solicitation analysis vs. proposal production | Today: Intelligence analyzes, Publisher assembles, human decides bid/no-bid between them; long term this seam is a future Bid/Proposal agent |
| 5 | Publisher ↔ Librarian | "Identifies source repositories / gathers inputs" vs. retrieval monopoly | Publisher requests inputs from Librarian; never self-serves from storage |
| 6 | Publisher ↔ Librarian | Draft custody vs. Library custody | Handoff at human approval: before approval, Publisher owns it; after, Librarian owns it; no shared custody |
| 7 | Receipt ↔ Librarian | Duplicate detection | Transaction-level dedup → Receipt Agent; document-level dedup → Librarian; write both into both constitutions |
| 8 | Receipt ↔ future Accounting | Categorization creep | Closed classification vocabulary; no GL codes, reconciliation, or aggregation |
| 9 | Dispatch Ops ↔ Mike | Broker workflow vs. binding commitments | Enumerate informational vs. binding communications; binding = hard gate |
| 10 | Dispatch Ops ↔ Manager | Ops "exception workflow" vs. Manager decision queue | Ops exception workflow handles operational recovery within its authority; anything needing approval or crossing its boundary terminates in the Manager's queue — one escalation channel, not two |
| 11 | IFTA ↔ future Compliance | "Audit support" | IFTA prepares packages only; audit correspondence is human; broader compliance stays a layer (see Section 6) |

## 3. MISSING HANDOFFS

1. **Intelligence → Manager decision queue.** Universally implied, nowhere stated. The single most important missing sentence in the worker summaries.
2. **Receipt Agent intake.** Who feeds it — Dispatch Ops, Mike, a watched folder, an email address? Still undefined after two rounds. Undefined intake means two workers will grow competing intake behaviors.
3. **Mileage records → IFTA Agent: producer unnamed.** IFTA now consumes mileage records (good — round-1 fix landed) but no worker summary says who produces them. Name Dispatch Ops as producer and define the record as jurisdiction-segmented miles per trip — if Ops emits raw route data instead, IFTA receives an input it cannot process.
4. **Expense Records → staging.** Accounting is deferred, so this output needs a defined parking place with a custodian (Librarian holding a staging area) until Accounting exists. Currently the records fall off the edge of the diagram.
5. **Publisher rejected drafts / failed QC.** No defined path — back to requester via the Manager's queue, with reason. Unstated failure paths become silent discards.
6. **IFTA exceptions → resolution.** Flagged exceptions must land in the decision queue with a human resolver; the summary names the exception list but not its route.
7. **Post-Library distribution.** Publisher's chain ends at "sends approved assets to Library." If any asset is meant to leave the company (proposal submission, posting, sending to a broker), that outbound step has no owner and no gate. If nothing ever leaves, state that; if things leave, gate it.

## 4. UNOWNED OUTPUTS

1. **Expense Records** — customer (Accounting) deferred; needs interim custodian and frozen schema so the future Accounting agent inherits clean history.
2. **Bid/opportunity recommendations** (Intelligence, via SAM) — no bid workflow owner exists. Until one does, these terminate at Mike via the decision queue, explicitly.
3. **IFTA exception lists** — produced, but no named resolver.
4. **Rejected drafts and QC failures** (Publisher) — no return path.
5. **Audit-trail / work-order logs** — if round 1's audit-log doctrine was adopted, someone must own the log store; natural owner is the Librarian (append-only, no worker may edit its own history).

## 5. RECOMMENDED BOUNDARY CLARIFICATIONS

One sentence each, suitable for insertion into worker constitutions:

1. **Manager:** routes work, tracks approvals, and protects attention; it does not approve, execute domain work, own external integrations, or commission workers, and silence from Mike is never consent.
2. **Intelligence:** delivers analysis and recommendations to the Manager's decision queue only; no recommendation is a work order, and bid/no-bid is always a human decision.
3. **Publisher:** manages production and conformance editing of assets it did not originate; it obtains all inputs through the Librarian and its approval routing always terminates at a human.
4. **Librarian:** applies promotion, retention, and access rules issued by Mike; it enforces policy and proposes policy but never authors policy in force.
5. **Dispatch Ops:** performs informational external communication freely; any communication that binds Level 1 Transport — rates, bookings, terms, signatures — requires human approval before transmission.
6. **Receipt Agent:** extracts and classifies into Fuel, Expense, and Evidence Records with transaction-level duplicate detection; it assigns no GL codes, performs no reconciliation, and renders no accounting judgment.
7. **IFTA Agent:** prepares worksheets, exceptions, and packages from supplied fuel and mileage records; it never adjusts source data, never corresponds with a tax authority, and never files or pays.

## 6. FUNCTIONS THAT SHOULD REMAIN LAYERS

1. **Reports** — deterministic query and rendering; already correctly a layer.
2. **Compliance calendar** — deadline tracking (IRP, 2290, insurance, maintenance, driver files) as a helper layer under Ops/Manager with human-owned deadlines; see Section 7 for its graduation tripwire.
3. **Integration layer** — credentials and API connections as plumbing owned by domain agents or a thin shared component; never an agent, never the Manager.
4. **Staging/holding areas** — Expense Record staging, print queue, human-review queues: storage locations with custodians, not workers.
5. **Audit trail / work-order log** — append-only infrastructure under Librarian custody; a log with agency would be a contradiction.
6. **Duplicate detection** — a function embedded in two workers (Receipt: transactions; Librarian: documents), not a standalone anything.

## 7. FUNCTIONS THAT MAY BECOME FUTURE AGENTS

1. **Accounting Agent** — currently deferred (correctly; see Section 8). Tripwire: when QuickBooks-plus-human stops keeping pace, or when categorization requests to the Receipt Agent become frequent enough to tempt scope creep.
2. **Compliance Agent** — currently a layer (correctly). Tripwire, as the doctrine already anticipates: winning government contract work (which brings FAR-grade compliance obligations), adding drivers, or a first audit event. Any one of the three justifies graduation.
3. **Bid/Proposal (Contracts) Agent** — currently incubating, unnamed, inside Intelligence (solicitation analysis: SAM, second pages, hidden requirements) and Publisher (proposal assembly). This is the clearest hidden agent in the system. It does not need to exist yet — but name the seam now, so that when government work scales, the extraction is a planned birth instead of a custody dispute between two frozen journeymen.
4. **Maintenance/Safety Agent** — no current footprint; will incubate inside Dispatch Ops (exception workflow) as equipment and driver count grow. Watch for it; do not build it.

**On questions 14 and 15 directly:** Accounting is correctly deferred — provided the Expense Record schema is frozen now and the Receipt Agent's vocabulary stays closed, deferral costs nothing and the future agent inherits clean data. Compliance is correctly deferred as a layer — provided deferral of the *agent* does not mean deferral of the *calendar*; the deadline-tracking layer must exist from day one, because a missed 2290 or lapsed insurance does not wait for architectural maturity.

## 8. FINAL BOUNDARY RECOMMENDATION

The seven-worker catalogue survives the stress test. No worker is misconceived, none should be demoted to a layer, and no new agent is needed now. Every "could it drift" question came back *yes, through a nameable door* — which is the good outcome, because nameable doors can be written shut, and every one of them closes with a sentence in a constitution rather than a redesign.

Priority order for closing them: **first**, the Dispatch Ops informational-vs-binding line — it is the only boundary whose failure signs a contract; **second**, remove "bridges external systems" from the Manager — it is the only failure that degrades every other boundary at once; **third**, the Intelligence single-customer rule, before SAM analysis starts flowing; **fourth**, split duplicate detection between Receipt (transactions) and Librarian (documents) before the first fuel-card statement meets its own receipts; **fifth**, the remaining handoffs in Section 3.

Adopt the seven clarification sentences in Section 5 into the worker constitutions, define the four missing handoffs that have owners waiting (Intelligence→queue, intake→Receipt, Ops→mileage→IFTA, Expense→staging), and the boundary layer of this architecture is ready to carry code.

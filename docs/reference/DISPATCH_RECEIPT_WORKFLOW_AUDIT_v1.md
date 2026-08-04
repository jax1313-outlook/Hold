# DISPATCH_RECEIPT_WORKFLOW_AUDIT_v1

Auditor role: trucking operations workflow auditor
Scope: Receipt Agent → IFTA Agent → future Accounting flow
Date: 2026-08-03
Authority: Advisory only. Mike Zachary is final authority.

---

## 1. VALIDATION SUMMARY

**Q1 — Receipt vs IFTA separation: correct.** Extraction is continuous clerk work; IFTA preparation is periodic, jurisdiction-aware, consequence-bearing. Different cadence, different failure modes, different approval weight. Sustained through four audits; settled.

**Q2 — Receipt vs Accounting separation: correct**, held in place by the round-2 closed-vocabulary rule. One sharpening: "Classify" in the Receipt Agent's verb list must mean *expense class* (fuel, DEF, meals, maintenance, supplies, tolls...) — a closed list Mike owns — never GL codes, never deductibility, never account mapping. The Accounting Queue is the right staging construct and matches the round-3 staging doctrine.

**Q3 — One-receipt-many-records: yes, it works, and it is the right model.** The container discovery is the most operationally important insight in the project. It needs three supports to be safe: (a) **parent-child linkage** — every derived record carries its Evidence Record ID; the container relationship is data, not convention; (b) **sum validation** — extracted line items plus tax must reconcile to the document total; mismatch is an exception, because a silent gap means a missed transaction; (c) **transaction-level dedup** — and note the intake list makes this worse than round 2 knew: the agent accepts pump receipts, fuel card statements, AND credit card statements, so one diesel purchase can arrive on THREE documents. Same transaction, three containers. Without a dedup key, v1 triples fuel.

**One genuine gap the doctrine has not addressed — the dual nature of fuel.** The routing diagram implies disjoint destinations: fuel → IFTA, expenses → Accounting. But diesel is *both* — it is the IFTA tax input AND the largest expense category on the books. If diesel lines produce only Fuel Records, QuickBooks never sees fuel cost and the P&L is missing its biggest line. Recommendation: a diesel line emits **two records** — a Fuel Record to the IFTA Agent and an Expense Record (category: fuel) to the Accounting Queue — cross-linked to each other and to the shared Evidence Record, so the books and the tax return are separately complete and mutually reconcilable. This must be decided before schemas freeze; it changes both record counts and reconciliation logic.

**Q9 — ambiguous line item:** never guess, and never hold the whole receipt hostage. Route what is certain; quarantine only the ambiguous line to the human review queue with a reference to the evidence image; record the human's ruling. A recurring ruling ("'SHOP SUP MISC' at this vendor = supplies") becomes a Trade Memory candidate under the round-3 rules — validated pattern, human-confirmed, inspectable. The diesel never waits on the bungee cord.

**Q10 — DEF: Accounting only, never IFTA.** DEF is not motor fuel — it is not propulsion fuel and carries no fuel tax; it goes into a separate tank feeding the exhaust system. If DEF gallons ever reach a Fuel Record they corrupt both the gallons total and the fleet MPG calculation, and a corrupted MPG is how IFTA returns get flagged. DEF is an Expense Record with its own category (kept distinct from generic supplies, because cost-per-mile reporting will want it).

**Q11 — Oil/additives: Accounting, tagged for the future.** There is no Maintenance agent (round 2: incubating inside Ops, do not build). Route as Expense Records with a maintenance category tag. The category field carries the future — when a Maintenance function is born it queries history by tag; no routing infrastructure should be built today for a worker that doesn't exist.

**Q12 — Meals: Accounting only, yes — with the category preserved and judgment withheld.** Driver meals carry special tax treatment (per-diem versus actual, and the DOT hours-of-service 80% deduction rule). That is precisely the accounting judgment the Receipt Agent is forbidden to make. It classifies "meals," attaches driver/date attribution, and stops. The human (or future Accounting Agent) decides treatment.

**Q13 — Original documents: always preserved, unconditionally.** Round 3 doctrine applies in full: Archive immediately on registration, immutable, *before* extraction begins — preservation must never depend on extraction success. Even confirmed duplicates are preserved: keep the document, suppress the transaction, mark the linkage. IFTA's four-year retention makes the scan the leaf of the audit chain.

**Q14 — QuickBooks routing: a connector layer.** Not the Manager — that is round 2's Door 1, the super-agent seed, and it stays closed. Not a future Accounting Agent — do not birth an agent to get a pipe. A connector layer is a thin, non-agent integration component: credentials, API calls, retries, idempotent posting, zero judgment. Flow: Accounting Queue → human approval (accounting writes are a hard gate from round 2) → connector → QuickBooks. When the Accounting Agent is eventually commissioned, it slots between queue and connector with no re-plumbing. This is the pattern for every future integration.

**Q15 — Too complex for v1? The core is right-sized; the edges are not.** Capture → extract → classify → route → preserve, plus quarterly IFTA prep, is one coherent spine and the highest-value automation in the company. Monthly IFTA reporting (IFTA is quarterly — monthly is an internal nicety), automated audit-package assembly, credit card statement intake, and even the live QuickBooks connector can all defer without weakening the spine.

**Q16 — smallest useful v1: see Section 7.** One sentence version: the diesel path end-to-end — receipt in, evidence archived, fuel and expense records out, exceptions to a human queue, one quarterly IFTA worksheet Mike can approve — with expenses staged for manual posting and everything else deferred.

## 2. REQUIRED FUEL RECORD FIELDS

IFTA audit requirements drive this list — an auditor must be able to verify each purchase from the record alone, then walk to the source image.

| Field | Why |
|---|---|
| record_id | identity, linkage |
| evidence_record_id | provenance — the audit chain (mandatory, round 3) |
| expense_record_id (cross-link) | the dual-record fuel decision above |
| purchase_date (and time if available) | IFTA requirement; quarter assignment |
| vendor_name | IFTA requirement (seller name) |
| vendor_address | IFTA requirement; jurisdiction derivation |
| **jurisdiction (state/province)** | THE IFTA field; derived from address, never guessed |
| fuel_type | diesel / gasoline / reefer — see routing table |
| **tractor_or_reefer flag** | reefer fuel is NOT propulsion fuel — excluded from IFTA gallons, possibly refund-eligible; mixing it in corrupts the return |
| volume + unit (gallons/liters) | IFTA requirement; Canadian purchases arrive in liters — store as-received plus normalized gallons |
| unit_price, total_amount, currency | verification, sum validation; CAD for Canadian fuel |
| taxes_included flag | pump price normally includes fuel tax; bulk fuel may not — different IFTA handling |
| unit_number (truck) | IFTA requirement (fleet attribution) |
| driver | attribution |
| odometer (optional) | strengthens MPG validation when present |
| payment_method / card_last4 | dedup key component; statement matching |
| receipt_or_invoice_number | dedup key component |
| dedup_key (derived) | vendor + date + amount + volume + card — transaction-level dedup lives HERE (round 2) |
| extraction_confidence + review_status | flagged records never proceed silently |
| schema_version | frozen contract, round 1 |

## 3. REQUIRED EXPENSE RECORD FIELDS

record_id; evidence_record_id (mandatory provenance); fuel_record_id cross-link where applicable; purchase_date; vendor_name; vendor_location; line_description (verbatim from document); **category from the closed vocabulary** (fuel, DEF, meals, oil/additives, maintenance, parts, truck wash, parking, tolls, supplies, miscellaneous — Mike owns this list, the agent may not extend it); amount; tax_amount if itemized; currency; payment_method / card_last4; unit_number; driver; load_id (optional — enables cost-per-load reporting later); dedup_key; status (staged / approved / posted); quickbooks_ref once posted; extraction_confidence + review_status; schema_version.

Deliberately absent: GL account code, deductibility, tax treatment, reimbursement status — all accounting judgments, all forbidden to the Receipt Agent by the round-2 boundary.

## 4. REQUIRED EVIDENCE RECORD FIELDS

evidence_record_id; archive_location of the immutable original; **file_hash** (integrity proof + document-level dedup — the Librarian's half of the round-2 dedup split); document_type (pump receipt / fuel card statement / credit card statement / invoice / CSV export / email attachment); vendor; document_date (business date) and capture_date (received date) — distinct fields, per round 3; statement_period (for statements); page_count; **derived_record_ids** — the container's children; this list is what makes one-receipt-many-records auditable in both directions; extraction_status (complete / partial / failed / duplicate-document); duplicate_of (when applicable — document preserved, transactions suppressed); reviewed_by + review_date when a human touched it; retention_class (minimum: IFTA four-year); schema_version.

## 5. EXCEPTION LIST

**Receipt Agent must detect (Q7):**
1. Unreadable or partial scan — quarantine whole document to human queue; evidence still archived.
2. Missing required field on a fuel line — no derivable jurisdiction, no volume: fuel record cannot be born incomplete.
3. Sum mismatch — line items + tax ≠ document total: something was missed or misread.
4. Suspected duplicate transaction — dedup key collision across receipt/statement/card-statement; suppress and flag, never silently drop (a false-positive dedup deletes a real purchase).
5. Unknown vendor format — new layout: process what parses, flag for pattern learning (apprenticeship path).
6. Unclassifiable line item — the Q9 flow: route the certain, quarantine the ambiguous line.
7. Currency/unit anomaly — CAD or liters detected: normalize with rate/factor recorded, flag if unclear.
8. Negative amounts — refunds and credits are real transactions needing reversed handling, not errors to discard.
9. Date anomaly — future dates, dates older than the open period, dates outside a statement's own period.
10. Missing unit attribution — multi-truck ambiguity: never guess which truck fueled.
11. Statement period overlap — two statements covering the same days: mass-duplicate risk.

**IFTA Agent must detect (Q8):**
1. Fuel purchased in a jurisdiction with zero recorded miles — physically impossible; mileage data gap.
2. Substantial miles in a jurisdiction with an implausible fuel gap in the trail.
3. **Fleet MPG out of band** — the single best whole-pipeline health check: quarterly MPG outside the plausible class-8 range (or swinging sharply versus prior quarters) means missing fuel records, missing miles, or reefer/DEF contamination.
4. Odometer discontinuities — gaps or overlaps between consecutive trips for a unit.
5. Active-truck days with no mileage records.
6. Fuel record with broken evidence linkage — unsupportable in audit; must be repaired before the worksheet closes.
7. Late-arriving documents dated in a closed quarter — amended-return territory: flag to human, never silently absorb into the current quarter.
8. Rate table version mismatch — quarter computed against superseded IFTA rates.
9. Reefer-flagged fuel appearing in propulsion gallons.
10. Corner-clipping jurisdictions — tiny mileage in a state with no fuel: legitimate, but auditors ask; annotate rather than suppress.

Every exception terminates in a human queue (round 2: one escalation channel). The IFTA Agent never adjusts source data to make a worksheet balance (round 2, Leak 1).

## 6. ROUTING RULES

| Line item | Record(s) emitted | Destination(s) |
|---|---|---|
| Diesel / gasoline (tractor propulsion) | **Fuel Record + Expense Record (fuel), cross-linked** | IFTA Agent AND Accounting Queue |
| Reefer fuel (flagged) | Expense Record (reefer fuel); Fuel Record only if refund-tracking is later enabled | Accounting Queue; never IFTA propulsion gallons |
| DEF | Expense Record (DEF category) | Accounting Queue only — never IFTA |
| Meals | Expense Record (meals; driver + date attached; no deductibility judgment) | Accounting Queue only |
| Oil, additives, batteries, parts, maintenance items | Expense Record (maintenance-tagged categories) | Accounting Queue; tag carries the future Maintenance function |
| Truck wash, parking, supplies, bungee cords, misc | Expense Record (respective category) | Accounting Queue |
| Tolls | Expense Record (tolls; load_id attached when known) | Accounting Queue |
| Every document, regardless of content | Evidence Record | Archive (immutable) + Library index |
| Ambiguous line | quarantined line → human review queue | rest of document routes normally |

Structural rules: one line item → one classification → one or more records; every record → exactly one Evidence Record parent; every fuel purchase reconcilable in both IFTA and the books through the cross-link.

## 7. RECOMMENDED V1 (smallest useful)

The diesel path, end to end, plus staged expenses:

1. **Intake:** individual receipts (photo/scan/PDF) + ONE fuel card statement format (whichever card Level 1 actually runs). That pair covers the dominant share of fuel data and forces the dedup mechanism to exist from day one — with only two overlapping sources instead of three.
2. **Evidence:** archive-on-registration, hash, Evidence Record, Library index. Non-negotiable in v1; this is the audit spine.
3. **Extraction:** fuel lines and expense lines from the closed category list; sum validation; dedup; dual-record fuel emission.
4. **Human review queue:** ambiguous lines, exceptions, low-confidence extractions. Built in v1, not bolted on — the queue IS the apprenticeship mechanism: every ruling trains the pattern library under round-3 Trade Memory rules.
5. **IFTA quarterly worksheet:** fuel by jurisdiction + mileage records from Dispatch Ops (jurisdiction-segmented — the round-2 contract) → worksheet + exception list → Mike approves. One real quarter prepared with human review of every number is the journeyman exam forming itself.
6. **Expenses:** staged to the Accounting Queue with categories; Mike posts to QuickBooks manually for now.

## 8. DEFERRED ITEMS

Credit card statement intake (the third overlapping source — add only after receipt+statement dedup is proven for one full quarter); the live QuickBooks connector (the queue works with a human posting; the connector layer slots in without re-plumbing); monthly IFTA reporting (quarterly is the legal rhythm; monthly is a Reports-layer nicety later); automated audit-package assembly (assemble manually the first time — doing it by hand once teaches what the automation must produce); reefer refund tracking (flag the fuel now, build the tracking if/when reefer operations warrant); email-inbox auto-intake and vendor-export formats (each new format enters through the apprenticeship queue, one at a time); the Accounting Agent itself (tripwire per round 2).

## 9. GO / NO-GO FOR CODING

**GO — for the Section 7 scope, with four pre-conditions, all writing rather than redesign:**

1. **Decide the dual-record fuel question** (Section 1) before freezing the Fuel and Expense Record schemas — it changes record counts, cross-links, and reconciliation.
2. **Freeze the three schemas** (Sections 2–4) as versioned contracts per round 1.
3. **Confirm the mileage record contract with Dispatch Ops** — jurisdiction-segmented miles per unit per period. The IFTA Agent's v1 is hostage to this input existing; if Ops tooling lags, v1 mileage can come from a human-entered worksheet in the same schema, which keeps the contract honest while the automation catches up.
4. **Define the closed expense-category vocabulary** — Mike authors it; the agent never extends it.

This is the first audit in the series to reach an unconditional GO on scope: the workflow is sound, the separations hold, the container model is right, and the smallest useful v1 is genuinely small while still removing the worst quarterly pain in the business. Build this one first.

# RECEIPT_CONSTITUTION_v1

**Status:** Adopted (boundary clause) + partially adopted (buildable
workflow scope). Operates under `CONSTITUTION.md` and
`DISPATCH_BASE_CONSTITUTION_v1.md`. Required before Lane C.

## Authority

Mike Zachary is final authority. This constitution binds the Receipt
Agent; it applies it, and never amends it.

## Boundary clause (#12 — APPROVED 2026-08-03)

Verbatim, `DISPATCH_BUILD_BLUEPRINT_v1` Part 2.2 item 6:

> **Receipt Agent:** extracts and classifies into Fuel, Expense, and
> Evidence Records with transaction-level duplicate detection; assigns
> no GL codes, performs no reconciliation, renders no accounting
> judgment; its classification vocabulary is closed (Contract 1.5).

"Classify" means expense class only (fuel, DEF, meals, maintenance...) —
never GL codes, never deductibility, never account mapping
(`DISPATCH_RECEIPT_WORKFLOW_AUDIT_v1` Q2). The categorization-creep
gradient (extract → classify → GL code → reconcile → financial
statements) stops at classify, by constitution, not by discipline alone.

## The container model

"A receipt is a container of business transactions" — the strongest
single design decision in the source material
(`DISPATCH_ARCHITECTURE_AUDIT_v1` Q11). One document may emit several
records. Three supports make it safe, all required in Lane C:

1. **Parent-child linkage** — every derived record carries its
   `evidence_record_id`.
2. **Sum validation** — extracted line items plus tax must reconcile to
   the document total; mismatch is an exception.
3. **Transaction-level dedup** — `dedup_key` per contract 1.2. The
   Receipt Agent owns this half of the dedup split; the Librarian owns
   document-level dedup via `file_hash`. Without it, the same diesel
   purchase arriving as a pump receipt AND a fuel-card statement line
   double-produces Fuel Records and corrupts the IFTA return.

## Routing table

Per `DISPATCH_RECEIPT_WORKFLOW_AUDIT_v1` Section 6:

| Line item | Record(s) emitted | Destination(s) |
|---|---|---|
| Diesel / gasoline (propulsion) | FuelRecord + ExpenseRecord (`fuel`), cross-linked — **HELD, see below** | IFTA Agent AND Accounting Queue |
| Reefer fuel (flagged) | ExpenseRecord (`reefer_fuel`) only | Accounting Queue; never IFTA propulsion gallons |
| DEF | ExpenseRecord (`def`) | Accounting Queue only — never IFTA, under any circumstance |
| Meals | ExpenseRecord (`meals`; driver + date attached; no deductibility judgment) | Accounting Queue only |
| Oil, additives, maintenance items | ExpenseRecord (maintenance-tagged category) | Accounting Queue |
| Truck wash, parking, supplies, tolls, misc | ExpenseRecord (respective category) | Accounting Queue |
| Every document, regardless of content | EvidenceRecord | Archive (immutable) + Library index |
| Ambiguous line | quarantined line → human review queue | rest of document routes normally |

## Explicit HELD markers — do not build these

- **#2 (dual-record fuel).** The router that actually emits FuelRecord +
  ExpenseRecord and writes those tables is BLOCKED. Extraction terminates
  in a `pending_routing` state: validated, classified line items with
  full provenance, awaiting the router. This is by design, not a gap.
- **#3 (closed expense vocabulary).** Category validation against a
  frozen list is BLOCKED — the list itself is not frozen. See
  `contracts/expense_vocabulary.HOLD.md`.
- **#14 (Trade Memory).** No pattern storage, no pattern reliance,
  anywhere. Every unknown format goes to the review queue; human rulings
  accumulate in the audit trail and can seed patterns later.

## Exception list (Receipt Agent must detect — `DISPATCH_RECEIPT_WORKFLOW_AUDIT_v1` Section 5)

Unreadable/partial scan; missing required field on a fuel line; sum
mismatch; suspected duplicate transaction (suppress + flag, never
silently drop); unknown vendor format; unclassifiable line item (route
the certain, quarantine the ambiguous line); currency/unit anomaly
(CAD/liters — normalize with rate/factor recorded); negative amounts
(refunds are real transactions, not errors); date anomaly; missing unit
attribution (never guess which truck); statement period overlap.

Every exception terminates in the Manager's queue (one escalation
channel). The Receipt Agent never guesses and never holds a whole
document hostage for one ambiguous line.

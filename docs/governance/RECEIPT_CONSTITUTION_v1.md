# RECEIPT_CONSTITUTION_v1

**Status:** Fully adopted. Operates under `CONSTITUTION.md` and
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

## Routing table (fully adopted — #2 and #3 approved 2026-08-04)

Per `DISPATCH_RECEIPT_WORKFLOW_AUDIT_v1` Section 6 and Decision D1
(`DISPATCH_BUILD_BLUEPRINT_v1` Part 1.2):

| Line item | Record(s) emitted | Destination(s) |
|---|---|---|
| Diesel / gasoline (propulsion) | FuelRecord + ExpenseRecord (`fuel`), cross-linked | IFTA Agent AND Accounting Queue |
| Reefer fuel (flagged) | ExpenseRecord (`reefer_fuel`) only | Accounting Queue; never IFTA propulsion gallons |
| DEF | ExpenseRecord (`def`) | Accounting Queue only — never IFTA, under any circumstance |
| Meals | ExpenseRecord (`meals`; driver + date attached; no deductibility judgment) | Accounting Queue only |
| Oil, additives, maintenance items | ExpenseRecord (maintenance-tagged category) | Accounting Queue |
| Truck wash, parking, supplies, tolls, misc | ExpenseRecord (respective category) | Accounting Queue |
| Every document, regardless of content | EvidenceRecord | Archive (immutable) + Library index |
| Ambiguous line | quarantined line → human review queue | rest of document routes normally |

Categories are validated against `contracts/expense_vocabulary.schema.json`
(FROZEN v1.0, approved AS WRITTEN 2026-08-04).

## Formerly-HELD items — now resolved in doctrine; still unbuilt (Lane C's job)

As of 2026-08-04, none of #2, #3, or #14 are held. This constitution now
fully authorizes:

- **The router** — code converting `pending_routing` items into real
  FuelRecord/ExpenseRecord rows per the routing table above. **Not yet
  built.** No lane session has run.
- **`fuel_records` / `expense_records` table creation** against the now-
  frozen schemas. **Not yet built.**
- **Category validation** against the frozen vocabulary. **Not yet
  built.**
- **Trade Memory** for the Receipt Agent, per the adopted doctrine in
  `MEMORY_DOCTRINE_v1.md`. **Not yet built.**

This section previously listed these as explicit HELD markers a build
session must not cross. They are retained here, reframed, so a future
Lane C session knows the doctrine is settled and the only remaining gap
is implementation.

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

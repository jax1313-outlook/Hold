# CONTRACT_REGISTER

The index a build session checks before trusting any schema. Source of
truth for every file in `contracts/`. Updated only by Mike's decision.

| Contract | File | Status | Version | Source |
|---|---|---|---|---|
| Config | `config.schema.json` | **FROZEN** | 1.0 | Blueprint 1.1. Storage mapping = approval item #1 (APPROVED 2026-08-03). |
| Evidence Record | `evidence_record.schema.json` | **FROZEN** | 1.0 | Blueprint 1.2. In force. |
| Mileage Record | `mileage_record.schema.json` | **FROZEN** | 1.0 | Blueprint 1.2. In force. |
| Queue Item | `queue_item.schema.json` | **FROZEN** | 1.0 | Blueprint 1.3. In force. |
| Archive/Evidence Interface | (behavioral — see `evidence_record.schema.json` `interface_note`) | **FROZEN** | 1.0 | Blueprint 1.4. In force. |
| Fuel Record | `fuel_record.schema.json` | **FROZEN** | 1.0 | Blueprint 1.2, Decision D1. Frozen 2026-08-04 on approval of #2. |
| Expense Record | `expense_record.schema.json` | **FROZEN** | 1.0 | Blueprint 1.2. Frozen 2026-08-04 on approval of #2 and #3. |
| Closed Expense Vocabulary | `expense_vocabulary.schema.json` | **FROZEN** | 1.0 | Blueprint 1.5. Frozen 2026-08-04, approved AS WRITTEN (#3). Library copy: `library_seed/Vocabulary/expense_vocabulary.v1.json`. |
| Audit Entry | `audit_entry.schema.json` | **FROZEN** | 1.0 | Blueprint 1.6. In force. |

All nine contracts are now FROZEN. No DRAFT or HELD-ABSENT contracts
remain as of 2026-08-04.

## Change history

- 2026-08-04 (seed): Five contracts frozen (config, evidence_record,
  mileage_record, queue_item, audit_entry). Two contracts held as drafts
  (fuel_record, expense_record). One contract held-absent
  (expense_vocabulary).
- 2026-08-04 (decision): #2 (dual-record fuel), #3 (closed expense
  vocabulary, as written), #4 (hard approval gates, as written), and #14
  (Trade Memory doctrine) approved. `fuel_record.DRAFT.json` →
  `fuel_record.schema.json` (FROZEN). `expense_record.DRAFT.json` →
  `expense_record.schema.json` (FROZEN). `expense_vocabulary.HOLD.md` →
  `expense_vocabulary.schema.json` (FROZEN) +
  `library_seed/Vocabulary/expense_vocabulary.v1.json` (installed Library
  copy). See `docs/decisions/DECISION_LOG.md` for the full record.

## Rule

A frozen contract changes only by Mike's decision, a version bump, and
same-day notice to every open lane (`DISPATCH_BUILD_BLUEPRINT_v1` Part 0).
A schema change discovered mid-build is escalated, never quietly patched
in one lane (`DISPATCH_BUILD_MATRIX_AUDIT_v1` Section 8).

## Hold Re-Entry Protocol status

Per the Execution Package's Hold Re-Entry Protocol: "#2 + #3 approved →
issue PACKET C-2 (Router & Freeze)." The freeze half of that trigger is
now done (this commit). The router itself — build code that converts
`pending_routing` items into real FuelRecord/ExpenseRecord rows — is Lane
C implementation work and has **not** been started; this repository seed
does not write application code. Packet C-2's router-building portion
remains open for a future Lane C build session.

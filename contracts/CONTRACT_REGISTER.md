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
| Closed Expense Vocabulary | `expense_vocabulary.HOLD.md` | **HELD-ABSENT** | — | Blueprint 1.5. Held on #3. Draft candidate list recorded, non-binding. |
| Audit Entry | `audit_entry.schema.json` | **FROZEN** | 1.0 | Blueprint 1.6. In force. |
| Fuel Record | `fuel_record.DRAFT.json` | **DRAFT — HELD** | 1.0-DRAFT | Blueprint 1.2. Held on #2 (D1 cross-link). |
| Expense Record | `expense_record.DRAFT.json` | **DRAFT — HELD** | 1.0-DRAFT | Blueprint 1.2. Held on #2 (cross-link) and #3 (category enum). |

## Change history

- 2026-08-04: Seeded. Five contracts frozen (config, evidence_record,
  mileage_record, queue_item, audit_entry) against
  `DISPATCH_BUILD_BLUEPRINT_v1` Part 1, which the Execution Package
  confirms as either an approved numbered item (#1) or explicitly "in
  force" (1.2 Evidence/Mileage, 1.3, 1.4, 1.6). Two contracts held as
  drafts (fuel_record, expense_record) per open items #2/#3. One
  contract held-absent (expense_vocabulary) per open item #3.

## Rule

A frozen contract changes only by Mike's decision, a version bump, and
same-day notice to every open lane (`DISPATCH_BUILD_BLUEPRINT_v1` Part 0).
A schema change discovered mid-build is escalated, never quietly patched
in one lane (`DISPATCH_BUILD_MATRIX_AUDIT_v1` Section 8).

## What freezes next (Hold Re-Entry Protocol)

On #2 + #3 approval: `fuel_record.DRAFT.json` and `expense_record.DRAFT.json`
freeze to v1.0 (dropping the DRAFT suffix and hold markers); a real
`expense_vocabulary` v1 data file replaces the HOLD marker; Packet C-2
opens.

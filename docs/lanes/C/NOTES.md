# Lane C — Receipt → IFTA Chain — NOTES

Branch: `build/receipt-ifta`. Packet: `docs/reference/DISPATCH_MATRIX_EXECUTION_PACKAGE_v1.md` Packet C.
Merges after Lane B.

Update this file at the end of every Lane C session. Do not delete prior
entries — append.

## Built

(nothing yet — seed only. No lane session has run.)

## Formerly blocked, now resolved in doctrine (2026-08-04) — still unbuilt

#2 (dual-record fuel), #3 (expense vocabulary), and #14 (Trade Memory)
are APPROVED as of 2026-08-04 — see `docs/decisions/DECISION_LOG.md`.
This removes the *doctrinal* block on the items below; none of them have
been *built*:

- The router (`pending_routing` → real records) — authorized, not built.
- `fuel_records` / `expense_records` table creation — schemas frozen
  (`contracts/fuel_record.schema.json`, `expense_record.schema.json`),
  tables not created.
- Category validation against `contracts/expense_vocabulary.schema.json`
  — vocabulary frozen, validation not implemented.
- ExpenseRecord emission and Accounting Queue staging — not built.
- Trade Memory pattern storage — doctrine adopted
  (`docs/governance/MEMORY_DOCTRINE_v1.md`), not built.

Note: `contracts/fuel_record.DRAFT.json` and `expense_record.DRAFT.json`
no longer exist — renamed to `fuel_record.schema.json` /
`expense_record.schema.json` on freeze.

## Flagged (held decisions / open questions encountered)

(nothing yet)

## Deliberately Not Built

(nothing yet beyond the Blocked section above)

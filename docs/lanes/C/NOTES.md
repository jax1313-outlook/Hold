# Lane C — Receipt → IFTA Chain — NOTES

Branch: `build/receipt-ifta`. Packet: `docs/reference/DISPATCH_MATRIX_EXECUTION_PACKAGE_v1.md` Packet C.
Merges after Lane B; its own merge may itself wait on #2/#3.

Update this file at the end of every Lane C session. Do not delete prior
entries — append.

## Built

(nothing yet — seed only)

## Blocked (explicit — pending #2 dual-record fuel / #3 expense vocabulary / #14 Trade Memory)

- The router (extraction terminates at `pending_routing`, not records).
- `fuel_records` / `expense_records` table creation and final schema freeze.
- Category validation against the closed expense vocabulary.
- ExpenseRecord emission and Accounting Queue staging.
- Any Trade Memory pattern storage or reliance (#14).

## Flagged (held decisions / open questions encountered)

(nothing yet)

## Deliberately Not Built

(nothing yet beyond the Blocked section above)

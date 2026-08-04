# APPROVAL_REGISTER

The single place approval truth lives for Dispatch Matrix Group 1. Updated
only by Mike Zachary's decisions. Source: `DISPATCH_MATRIX_EXECUTION_PACKAGE_v1`
"APPROVAL STATUS THIS PACKAGE RESPECTS" (approval status of 2026-08-03).

**Status note:** the detailed clause text behind each item lives in
`DISPATCH_BUILD_BLUEPRINT_v1`, which was not provided to this seeding
session. This register records item number, short title, status, and date
only — exactly what the Execution Package states. Full clause text is
`PENDING SOURCE` until the blueprint is supplied; see
`docs/reference/README.md`.

| # | Title | Status | Date | Source |
|---|---|---|---|---|
| 1 | Storage mapping | APPROVED | 2026-08-03 | DISPATCH_MATRIX_EXECUTION_PACKAGE_v1 |
| 2 | Dual-record fuel (D1 cross-link field) | **HELD** | 2026-08-03 | DISPATCH_MATRIX_EXECUTION_PACKAGE_v1 |
| 3 | Closed expense vocabulary | **HELD** | 2026-08-03 | DISPATCH_MATRIX_EXECUTION_PACKAGE_v1 |
| 4 | Hard approval gates | **HELD** | 2026-08-03 | DISPATCH_MATRIX_EXECUTION_PACKAGE_v1 |
| 5 | Failure doctrine | APPROVED | 2026-08-03 | DISPATCH_MATRIX_EXECUTION_PACKAGE_v1 |
| 6 | Deletion / retention doctrine | APPROVED | 2026-08-03 | DISPATCH_MATRIX_EXECUTION_PACKAGE_v1 |
| 7 | Worker boundary clause — Manager (per Packet B) | APPROVED | 2026-08-03 | DISPATCH_MATRIX_EXECUTION_PACKAGE_v1 |
| 8 | Worker boundary clause — worker not identified in provided source (PENDING SOURCE) | APPROVED | 2026-08-03 | DISPATCH_MATRIX_EXECUTION_PACKAGE_v1 (number and status only) |
| 9 | Worker boundary clause — worker not identified in provided source (PENDING SOURCE) | APPROVED | 2026-08-03 | DISPATCH_MATRIX_EXECUTION_PACKAGE_v1 (number and status only) |
| 10 | Worker boundary clause — Librarian (per Packet A) | APPROVED | 2026-08-03 | DISPATCH_MATRIX_EXECUTION_PACKAGE_v1 |
| 11 | Worker boundary clause — worker not identified in provided source (PENDING SOURCE) | APPROVED | 2026-08-03 | DISPATCH_MATRIX_EXECUTION_PACKAGE_v1 (number and status only) |
| 12 | Worker boundary clause — Receipt (per Packet C) | APPROVED | 2026-08-03 | DISPATCH_MATRIX_EXECUTION_PACKAGE_v1 |
| 13 | Worker boundary clause — IFTA (per Packet C) | APPROVED | 2026-08-03 | DISPATCH_MATRIX_EXECUTION_PACKAGE_v1 |
| 14 | Trade Memory doctrine | **HELD** | 2026-08-03 | DISPATCH_MATRIX_EXECUTION_PACKAGE_v1 |

Also stated **in force** (not numbered approval items, but treated as
settled per the Execution Package): queue item contract 1.3,
archive/evidence interface 1.4, audit entry format 1.6, EvidenceRecord and
MileageRecord schemas, IFTA computation spec 3.5. Field-level content for
these is `PENDING SOURCE` in `contracts/` — see `contracts/CONTRACT_REGISTER.md`.

**Consequences (from the Execution Package, still in force):**
FuelRecord/ExpenseRecord schemas are NOT frozen (cross-link field and
category validation pend #2/#3); the Lane C router is BLOCKED; Trade
Memory is EXCLUDED from all packets; the Base Constitution hard-gate
amendment is a document milestone pending #4 (blocks the first merge into
`integration`, not lane builds).

Items #8, #9, #11 are recorded here only because the Execution Package
states "seven worker boundary clauses" span #7–#13 and names four of the
seven workers explicitly (Manager=#7, Librarian=#10, Receipt=#12,
IFTA=#13). Which workers #8, #9, #11 belong to is not stated in either
document provided to this seeding session. Do not assume — confirm with
Mike or the blueprint before relying on these three.

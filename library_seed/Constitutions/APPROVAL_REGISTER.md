# APPROVAL_REGISTER

The single place approval truth lives for Dispatch Matrix Group 1.
Updated only by Mike Zachary's decisions. Source:
`DISPATCH_MATRIX_EXECUTION_PACKAGE_v1` "APPROVAL STATUS THIS PACKAGE
RESPECTS" (approval status of 2026-08-03), cross-referenced against
`DISPATCH_BUILD_BLUEPRINT_v1` Part 2.2 for the seven worker boundary
clauses' exact identities, updated 2026-08-04 for the resolution of
#2/#3/#4/#14.

| # | Title | Status | Date | Source |
|---|---|---|---|---|
| 1 | Storage mapping | APPROVED | 2026-08-03 | Blueprint 1.1 |
| 2 | Dual-record fuel (D1 cross-link field) | **APPROVED** | 2026-08-04 | Blueprint 1.2 Decision D1 |
| 3 | Closed expense vocabulary | **APPROVED AS WRITTEN** | 2026-08-04 | Blueprint 1.5 |
| 4 | Hard approval gates | **APPROVED AS WRITTEN** | 2026-08-04 | Blueprint 2.1 |
| 5 | Failure doctrine | APPROVED | 2026-08-03 | Blueprint 2.1 |
| 6 | Deletion / retention doctrine | APPROVED | 2026-08-03 | Blueprint 2.1 |
| 7 | Worker boundary clause — Manager | APPROVED | 2026-08-03 | Blueprint 2.2 item 1 |
| 8 | Worker boundary clause — Intelligence | APPROVED | 2026-08-03 | Blueprint 2.2 item 2 |
| 9 | Worker boundary clause — Publisher | APPROVED | 2026-08-03 | Blueprint 2.2 item 3 |
| 10 | Worker boundary clause — Librarian | APPROVED | 2026-08-03 | Blueprint 2.2 item 4 |
| 11 | Worker boundary clause — Dispatch Ops | APPROVED | 2026-08-03 | Blueprint 2.2 item 5 |
| 12 | Worker boundary clause — Receipt Agent | APPROVED | 2026-08-03 | Blueprint 2.2 item 6 |
| 13 | Worker boundary clause — IFTA Agent | APPROVED | 2026-08-03 | Blueprint 2.2 item 7 |
| 14 | Trade Memory doctrine | **APPROVED** | 2026-08-04 | Blueprint 2.3 |

**All 14 items are now APPROVED.** No open holds remain as of 2026-08-04.
See `docs/decisions/DECISION_LOG.md` for the resolution record of
#2/#3/#4/#14, including a provenance note on how that approval was
communicated in this session.

**In force (not numbered approval items, but settled per the Execution
Package and confirmed verbatim in the blueprint):** queue item contract
1.3, archive/evidence interface 1.4, audit entry format 1.6, EvidenceRecord
and MileageRecord schemas (1.2), IFTA computation spec 3.5. See
`contracts/CONTRACT_REGISTER.md`.

## What approval unblocks vs. what is still unbuilt

Approval resolves *documentation and contract* status — it does not
itself write code. As of 2026-08-04:

- All nine data contracts are FROZEN (`contracts/CONTRACT_REGISTER.md`).
- `DISPATCH_BASE_CONSTITUTION_v1.md`'s Hard Approval Gates section and
  `MEMORY_DOCTRINE_v1.md`'s Trade Memory section are filled and adopted.
- The Lane C router, FuelRecord/ExpenseRecord table creation, category
  validation logic, and any Trade Memory component remain **unbuilt**.
  No lane build session (A, B, C, or D) has been opened. This register
  records legal/decision status, not build status — see
  `docs/lanes/*/NOTES.md` for build status, which stays "nothing yet —
  seed only" until a lane session actually runs.

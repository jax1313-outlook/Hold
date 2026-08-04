# HOLD_PRE_BUILD_v1

Purpose: baseline status report — a point-in-time snapshot of the Hold
repository immediately before any lane build session opens.
Repository: `jax1313-outlook/hold`.
Authority: Mike Zachary is final authority. This document is a status
report; it contains no implementation code and adopts nothing on its
own — it records adoptions already made elsewhere
(`docs/decisions/DECISION_LOG.md`).

---

## 1. Current commit

| | |
|---|---|
| Commit | `3888ab8a8cfc89d768b33794030f5022fef42a48` |
| Date | 2026-08-04 02:25:47 +0000 |
| Subject | "README: clarify main's pre-lane commit window" |
| State | All branches below point at this same commit — nothing is stale relative to it. |

## 2. Branch structure

```
main                        3888ab8
 └── integration             3888ab8
      ├── build/librarian-spine   3888ab8   (Lane A — not yet opened)
      ├── build/manager-queue     3888ab8   (Lane B — not yet opened)
      ├── build/receipt-ifta      3888ab8   (Lane C — not yet opened)
      └── build/reports           3888ab8   (Lane D — not yet opened)

claude/new-session-916rfj   3888ab8   (this session's working branch)
```

All seven branches are identical at this commit. No lane branch has ever
diverged — no lane build session has been opened. Per `README.md`'s
branch discipline: `main` accepts direct seed/decision-record commits
only until Lane A's build begins; after that, only validated
`integration` merges land on `main`, and no lane commits directly to
`main` or `integration`.

## 3. Approved contracts

All nine contracts in `contracts/` are **FROZEN v1.0**. None remain DRAFT
or HELD-ABSENT.

| Contract | File | Version | Approval basis |
|---|---|---|---|
| Config | `config.schema.json` | 1.0 | Blueprint 1.1; approval item #1 |
| Evidence Record | `evidence_record.schema.json` | 1.0 | Blueprint 1.2; in force |
| Mileage Record | `mileage_record.schema.json` | 1.0 | Blueprint 1.2; in force |
| Queue Item | `queue_item.schema.json` | 1.0 | Blueprint 1.3; in force |
| Archive/Evidence Interface | behavioral, in `evidence_record.schema.json` | 1.0 | Blueprint 1.4; in force |
| Fuel Record | `fuel_record.schema.json` | 1.0 | Blueprint 1.2, Decision D1; approval item #2 (2026-08-04) |
| Expense Record | `expense_record.schema.json` | 1.0 | Blueprint 1.2; approval items #2 + #3 (2026-08-04) |
| Closed Expense Vocabulary | `expense_vocabulary.schema.json` | 1.0 | Blueprint 1.5; approval item #3, AS WRITTEN (2026-08-04). Library copy: `library_seed/Vocabulary/expense_vocabulary.v1.json`. |
| Audit Entry | `audit_entry.schema.json` | 1.0 | Blueprint 1.6; in force |

Source of truth: `contracts/CONTRACT_REGISTER.md`. A frozen contract
changes only by Mike's decision, a version bump, and same-day notice to
every open lane.

## 4. Approved constitutions

All documents in `docs/governance/` are adopted (fully, except where
noted):

| Document | Status | Covers |
|---|---|---|
| `DISPATCH_BASE_CONSTITUTION_v1.md` | **Fully adopted** | Authority hierarchy; storage mapping (#1); Hard Approval Gates (#4, as written); Failure Doctrine (#5); Deletion & Retention Doctrine (#6) |
| `LIBRARIAN_CONSTITUTION_v1.md` | Adopted | Boundary clause #10; Evidence Spine scope (Lane A); document-level dedup; Trade Memory custody role (#14) |
| `MANAGER_CONSTITUTION_v1.md` | Adopted | Boundary clause #7; the three doors closed; Work Queue scope (Lane B) |
| `RECEIPT_CONSTITUTION_v1.md` | Adopted | Boundary clause #12; container model; routing table (fully adopted per D1/#3); exception list |
| `IFTA_CONSTITUTION_v1.md` | Adopted | Boundary clause #13; computation spec 3.5; exception list; fuel input adapter no longer provisional |
| `REPORTS_CHARTER_v1.md` | Adopted | Two bright lines; template/snapshot doctrine; v1 scope including Expense Summary (#3) |
| `APPROVAL_REGISTER.md` | Current | Single source of truth for all 14 approval items — all APPROVED |

## 5. Approved doctrines

| # | Doctrine | Status | Date |
|---|---|---|---|
| 1 | Storage mapping (OPERATIONS/LIBRARY/ARCHIVE tiers, "Memory" retired as a tier name) | APPROVED | 2026-08-03 |
| 2 | Dual-record fuel (Decision D1) | APPROVED | 2026-08-04 |
| 3 | Closed expense vocabulary (13 categories) | APPROVED AS WRITTEN | 2026-08-04 |
| 4 | Hard approval gates (7 gates) | APPROVED AS WRITTEN | 2026-08-04 |
| 5 | Failure doctrine (stop, quarantine, escalate) | APPROVED | 2026-08-03 |
| 6 | Deletion & retention doctrine (no worker deletes; only Mike destroys) | APPROVED | 2026-08-03 |
| 7–13 | Seven worker boundary clauses (Manager, Intelligence, Publisher, Librarian, Dispatch Ops, Receipt, IFTA) | APPROVED | 2026-08-03 |
| 14 | Trade Memory doctrine (closed entry types, freeze-at-journeyman semantics, promotion path) | APPROVED | 2026-08-04 |

**Recommended but not approved items** (audit content, not numbered
approval items — do not treat as adopted): the general Company Memory
lifecycle (draft → candidate → approved → archived), the operational
definition of Freeze / journeyman-exam mechanics, the storage read/write
matrix, and the off-drive backup doctrine. These remain in
`docs/reference/` as advisory recommendations only.

## 6. Open items

**None.** All 14 numbered approval items are resolved as of 2026-08-04.
`docs/decisions/DECISION_LOG.md`'s Open section is empty.

## 7. What this baseline does not include

Per instruction, this report contains no implementation code. As of this
commit:

- No lane build session (A, B, C, or D) has been opened.
- `src/dispatch/**` and `tools/**` contain only placeholder files.
- No production Dispatch system or `D:\` operational root has been
  touched by this repository at any point.
- One non-decision gap remains outside this report's scope: real IFTA
  per-jurisdiction rate data for `library_seed/RateTables/` — needed
  before Lane C's validation gate, not before Lane A/B/C/D open. See
  `library_seed/RateTables/README.md`.

---

*End of HOLD_PRE_BUILD_v1. Status report only; contains no
implementation code and no adoption not already recorded in
`docs/decisions/DECISION_LOG.md`.*

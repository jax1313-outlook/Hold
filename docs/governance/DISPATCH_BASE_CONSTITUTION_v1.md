# DISPATCH_BASE_CONSTITUTION_v1

**Status:** Partially adopted. Operates under `CONSTITUTION.md` (Level 1
Transport Inc. master constitution), whose Article 0 controls in any
conflict. This document does not compete with, replace, or sit above
`CONSTITUTION.md` — it is the Dispatch-project-scoped constitution the
Hold Seed Package requires before Lane A opens.

**Seeding note:** `DISPATCH_BUILD_BLUEPRINT_v1`, the source for the full
clause text of items #1, #5, #6 below, was not provided to the session
that seeded this repository. This document records the authority
hierarchy (sourced from `CONSTITUTION.md` and the Execution Package) in
full, and everything the two provided documents actually state about #1,
#5, #6 — nothing more. Sections marked `PENDING SOURCE` must not be
treated as complete or frozen.

## Article I — Authority Hierarchy

Per `CONSTITUTION.md` Article I: the human owner is final authority for
business, architecture, scoring doctrine, role boundaries, source access,
external communications, business commitments, implementation approval,
and constitutional amendments. Within the Dispatch Matrix program, that
authority is Mike Zachary (per `DISPATCH_MATRIX_EXECUTION_PACKAGE_v1`,
"Authority: Mike Zachary is final authority. This package contains no
implementation code.").

No AI system, builder, code module, agent, automation, or tool may
override this. A build session that believes a contract or doctrine is
wrong records it in its lane `NOTES.md` and stops that thread — it never
edits `contracts/` or this document. Amendments happen only by Mike's
deliberate decision, recorded in `docs/decisions/DECISION_LOG.md`.

## #1 — Storage Mapping (APPROVED, 2026-08-03)

**STATUS: PENDING SOURCE.** The Execution Package confirms this item is
approved and "in force," and that the config loader must refuse to run in
sandbox mode against any root resolving under a production `D:\` path.
`DISPATCH_HOLD_SEED_PACKAGE_v1` §1 additionally states the Hold repository
itself must live outside the three operational roots (`D:\Dispatch
Operations`, `D:\Memory`, `D:\Archive`), and that sandbox data roots (e.g.
`D:\DispatchSandbox\{Operations,Library,Archive}`) live outside the
repository, named only in `config/sandbox.config.json`. The full mapping
(which logical store maps to which physical root, in both sandbox and
production) is not stated in either provided document.

## #5 — Failure Doctrine (APPROVED, 2026-08-03)

**STATUS: PENDING SOURCE**, with the following constraints actually
stated across the two provided documents and binding meanwhile:

- Nothing is ever silently discarded or auto-resolved. Exceptions route to
  the Manager queue (contract 1.3), never resolved by code alone.
- Registration failure on intake ⇒ quarantine + exception queue item,
  never a dropped file.
- Retrieval hash mismatch ⇒ raise + enqueue an exception queue item, never
  a silent return of unverified data.
- Duplicate-hash on registration ⇒ return the existing record flagged
  `duplicate_document`, never a second copy and never a silent no-op.
- Sum-validation mismatches, dedup collisions, and low-confidence
  extractions all become flagged exceptions, never silently dropped or
  silently accepted.

## #6 — Deletion & Retention Doctrine (APPROVED, 2026-08-03)

**STATUS: PENDING SOURCE**, with the following constraints actually
stated and binding meanwhile:

- No update and no delete path exists for archived evidence files,
  `evidence_records`, or `audit_log` rows — permanently, by design, not by
  configuration.
- The database bootstrap installs delete-revoking triggers on
  `evidence_records` and `audit_log`.
- Queue items are never deleted; decided items (approved/rejected/
  resolved) are retained permanently with their notes.
- Retention class defaulting exists for evidence records (mechanism not
  detailed in provided source).

## HARD APPROVAL GATES — HELD (#4), reserved, adoption pending

This section is intentionally empty. #4 (hard approval gates) is an open
hold — see `docs/decisions/DECISION_LOG.md`. Its absence here is not an
oversight and must not be read as either approval or rejection. On
Mike's decision, this section is adopted, the document version is
stamped, and the first merge into `integration` is cleared (validation
gate 6, docs-match-as-built) per the Execution Package's Hold Re-Entry
Protocol.

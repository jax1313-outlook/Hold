# DISPATCH_BASE_CONSTITUTION_v1

**Status:** Fully adopted as of 2026-08-04. Operates under `CONSTITUTION.md`
(Level 1 Transport Inc. master constitution), whose Article 0 controls in
any conflict. This document does not compete with, replace, or sit above
`CONSTITUTION.md` — it is the Dispatch-project-scoped constitution the
Hold Seed Package requires before Lane A opens.

## Article I — Authority Hierarchy

Per `CONSTITUTION.md` Article I: the human owner is final authority for
business, architecture, scoring doctrine, role boundaries, source access,
external communications, business commitments, implementation approval,
and constitutional amendments. Within the Dispatch Matrix program, that
authority is Mike Zachary.

No AI system, builder, code module, agent, automation, or tool may
override this. A build session that believes a contract or doctrine is
wrong records it in its lane `NOTES.md` and stops that thread — it never
edits `contracts/` or this document. Amendments happen only by Mike's
deliberate decision, recorded in `docs/decisions/DECISION_LOG.md`.

## #1 — Storage Mapping (APPROVED, 2026-08-03)

Verbatim, `DISPATCH_BUILD_BLUEPRINT_v1` Part 1.1:

The word "Memory" is retired as a tier name. Three logical tiers, three
physical roots:

| Logical tier | Meaning | Physical root |
|---|---|---|
| OPERATIONS | living system — open-period records, queues, trade memory, print queue, intake | `D:\Dispatch Operations` |
| LIBRARY | approved truth — constitutions, templates, procedures, vocabulary, rate tables, evidence index | `D:\Memory\Library` |
| ARCHIVE | history — immutable originals, sealed bundles, report snapshots, audit rolls | `D:\Archive` |

Trade Memory is per-worker working knowledge and lives under OPERATIONS
(`Workers\<name>\TradeMemory\`), inspectable, never secret. All paths come
from `dispatch.config.json` (`contracts/config.schema.json`). No
component ever hardcodes a root. A component must refuse to start if
`environment` is `sandbox` but any root resolves under a production path.

## #4 — Hard Approval Gates (APPROVED AS WRITTEN, 2026-08-04)

Verbatim, `DISPATCH_BUILD_BLUEPRINT_v1` Part 2.1. No worker constitution
may weaken any of these seven gates:

1. No government filing or submission of any kind without explicit human
   approval.
2. No write to any accounting system (QuickBooks or successor) without
   explicit human approval.
3. No externally binding communication — rate acceptance, load booking or
   cancellation, contract terms, signatures, or any "accept" action —
   without explicit human approval. Informational communication (status,
   ETA, check calls, transmission of already-approved documents) is not
   gated.
4. No demotion, deletion, or in-place modification of promoted truth in
   the Library. Change is by supersession only, through the Librarian,
   with human approval.
5. No amendment to any constitution except by Mike Zachary, with a
   version increment.
6. No creation, modification, or retirement of any worker or helper
   layer except by Mike Zachary.
7. Approval is an affirmative act recorded in the decision queue.
   Silence, timeout, or absence is never consent.

Approved via direct instruction in this session, 2026-08-04. Per the
Execution Package's Hold Re-Entry Protocol, #4's approval clears the
first merge into `integration` (validation gate 6, docs-match-as-built)
— though no lane build has occurred yet, so no merge is currently
pending.

## #5 — Failure Doctrine (APPROVED, 2026-08-03)

Verbatim, `DISPATCH_BUILD_BLUEPRINT_v1` Part 2.1:

> On any failure, ambiguity, or boundary conflict, a worker stops the
> affected work item, quarantines it unchanged, posts it to the
> Manager's decision queue with reason and evidence references, and
> continues unaffected work. No worker may silently skip, guess,
> discard, or retry-past a failing item. No worker may modify source
> data to make its own output balance.

## #6 — Deletion & Retention Doctrine (APPROVED, 2026-08-03)

Verbatim, `DISPATCH_BUILD_BLUEPRINT_v1` Part 2.1:

> No worker deletes anything, anywhere, ever. The Librarian archives.
> Only Mike destroys, and never inside a statutory retention window
> (IFTA evidence: 4 years minimum; default class on all financial
> evidence).

Enforcement: the database bootstrap installs delete-revoking triggers on
`evidence_records` and `audit_log` (and all record tables — updates
allowed only on whitelisted status/review fields via views). No update,
no delete code path exists on archived files, `evidence_records`, or
`audit_log`, period.

## Amendment history

- 2026-08-03: Seeded partially adopted (#1, #5, #6). Hard Approval Gates
  section reserved and empty pending #4.
- 2026-08-04: #4 approved as written. Hard Approval Gates section filled.
  Document now fully adopted.

# MEMORY_DOCTRINE_v1

**Status:** Partially adopted. Operates under `CONSTITUTION.md` and
`DISPATCH_BASE_CONSTITUTION_v1.md`. Required before Lane A.

## Tier definitions and mapping (#1 — APPROVED, 2026-08-03)

Adopted in full in `DISPATCH_BASE_CONSTITUTION_v1.md` #1 — three logical
tiers (OPERATIONS, LIBRARY, ARCHIVE), one physical root each, "Memory"
retired as a tier name. See that document; not repeated here to avoid two
sources of truth.

## Lifecycle (recommended — `DISPATCH_MEMORY_AUDIT_v1` Section 5, not a numbered approval item)

**Status: RECOMMENDED, not confirmed adopted.** This is audit content
(advisory), not one of the items the Execution Package lists as approved
or in force. Recorded here in full because it is well-formed and likely
to be adopted, but no lane may treat it as binding until it appears in an
approved decision.

Knowledge/asset track: **Draft** (mutable, workspace, owned by
originator) → **Candidate** (submitted for approval, frozen as submitted)
→ **Approved** (human approves; Librarian promotes into Library;
immutable from this moment — change means supersession) → **Archived**
(on supersession/expiration/retirement; append-only; no worker deletes,
only Mike destroys, outside statutory windows).

Transactional track (skips the Library — records are facts, not
truth-claims): **Extracted** (Receipt Agent, provenance-linked,
dedup-checked) → **Validated** (passes contract checks or flags to the
human queue) → **Consumed** (read by IFTA Agent / QuickBooks posting
during the open period) → **Sealed** (period closes with human approval;
bundle archives together).

Confirmed by the actually-in-force contracts (not merely recommended):
evidence records: `register → retrieve / link_children`, no update/delete
ever; queue items: `open → in_review → approved / rejected / resolved`;
receipt line items: extraction terminates in `pending_routing` (held,
awaiting the router); IFTA packages: `DRAFT → seal-on-approval`.

## TRADE MEMORY — HELD (#14), reserved

This section is intentionally empty. #14 (Trade Memory doctrine) is an
open hold — see `docs/decisions/DECISION_LOG.md`. No pattern storage and
no pattern reliance exists anywhere in Dispatch Matrix Group 1 while this
section is empty. Every unknown format goes to the review queue; human
rulings accumulate in the audit trail and can seed patterns later.

**Draft text exists** and can be reviewed at
`docs/reference/DISPATCH_BUILD_BLUEPRINT_v1.md` Part 2.3 ("Trade Memory
rules") — physical home (`OPERATIONS\Workers\<name>\TradeMemory\`,
human-readable JSON, inspectable); a closed entry-type system
(`format_pattern` | `exception_pattern` | `efficiency_note` |
`validated_shortcut`); the rule that Trade Memory may optimize HOW a
worker checks, never WHETHER it checks; freeze-at-journeyman-certification
semantics (snapshot, read-only after, proposals queue for post-freeze
lessons); and the promotion path (worker proposes → Librarian routes →
Mike approves → enters Library). That text is drafted for Mike's
sign-off; it is not adopted by being drafted, and is not copied into this
section until Mike says so.

On approval: Packet C-3 (Trade Memory) is issued before any journeyman
certification, seeded from human rulings already accumulated in the audit
trail.

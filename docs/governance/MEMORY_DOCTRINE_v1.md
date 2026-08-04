# MEMORY_DOCTRINE_v1

**Status:** Fully adopted as of 2026-08-04 (tier mapping + Trade Memory).
General Company Memory lifecycle remains a documented recommendation, not
a numbered approval item — see that section below. Operates under
`CONSTITUTION.md` and `DISPATCH_BASE_CONSTITUTION_v1.md`. Required before
Lane A.

## Tier definitions and mapping (#1 — APPROVED, 2026-08-03)

Adopted in full in `DISPATCH_BASE_CONSTITUTION_v1.md` #1 — three logical
tiers (OPERATIONS, LIBRARY, ARCHIVE), one physical root each, "Memory"
retired as a tier name. See that document; not repeated here to avoid two
sources of truth.

## Lifecycle (recommended — `DISPATCH_MEMORY_AUDIT_v1` Section 5, not a numbered approval item)

**Status: RECOMMENDED, not confirmed adopted.** This is audit content
(advisory), not one of the 14 numbered approval items. Unlike #2/#3/#4/#14,
this was not part of the 2026-08-04 approval batch — recorded here in
full because it is well-formed and likely to be adopted, but no lane may
treat it as binding until it appears in an approved decision.

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
receipt line items: extraction terminates in `pending_routing` until the
router runs; IFTA packages: `DRAFT → seal-on-approval`.

## TRADE MEMORY (#14 — APPROVED, 2026-08-04)

Verbatim, `DISPATCH_BUILD_BLUEPRINT_v1` Part 2.3:

> Trade Memory lives at `OPERATIONS\Workers\<name>\TradeMemory\` as
> human-readable JSON; inspectable by Mike and the audit trail at all
> times. Entry types are closed: `format_pattern` | `exception_pattern` |
> `efficiency_note` | `validated_shortcut`. Anything rule-shaped ("always
> route X to Y", "skip check when...") is rejected at write time and
> escalated as a proposal. Patterns are hypotheses: validated by human
> confirmation during apprenticeship, and a pattern that stops matching
> flags — it never force-fits. Trade Memory may optimize HOW a worker
> checks, never WHETHER it checks. **At journeyman certification, Trade
> Memory is snapshotted and becomes read-only; post-freeze lessons queue
> as proposals for human-approved incorporation followed by
> re-certification against the regression suite.** Promotion path: worker
> proposes → Librarian routes → Mike approves → enters Library as
> company knowledge.

Approved via direct instruction in this session, 2026-08-04. Per the Hold
Re-Entry Protocol, Packet C-3 (Trade Memory) may now be issued before any
journeyman certification, seeded from human rulings already accumulated
in the audit trail — but no worker has reached journeyman status and no
Trade Memory component has been built. This is a documentation adoption,
not an implementation.

## Amendment history

- 2026-08-03: Seeded partially adopted (#1). Trade Memory section
  reserved and empty pending #14.
- 2026-08-04: #14 approved. Trade Memory section filled. Tier mapping and
  Trade Memory doctrine now fully adopted; the general lifecycle model
  (Section above) remains a recommendation, not an approved item.

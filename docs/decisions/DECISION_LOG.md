# DECISION_LOG

Seeded 2026-08-04 with four open entries, per `DISPATCH_HOLD_SEED_PACKAGE_v1`
§2. Each entry gets its own file here (`DECISION_<n>_<slug>.md`) once
resolved. No open session ever absorbs a decision mid-build — sessions end,
follow-on packets begin, per the Execution Package's Hold Re-Entry
Protocol.

## Resolved

### #2 — Dual-record fuel (D1 cross-link field) — APPROVED, 2026-08-04

Decision D1 adopted: a propulsion-fuel line item emits BOTH a FuelRecord
(→ IFTA) and an ExpenseRecord, category `fuel` (→ Accounting Queue),
cross-linked, sharing one EvidenceRecord parent. Reefer-flagged fuel
emits an ExpenseRecord only (category `reefer_fuel`). DEF is never a
FuelRecord. Recorded via direct instruction in this session, 2026-08-04
("#2 Dual-Record Fuel Doctrine — APPROVED").

**Unblocked:** `contracts/fuel_record.schema.json` and
`contracts/expense_record.schema.json` frozen v1.0. The Lane C router
(code that converts `pending_routing` items into these records) is now
authorized but **not built** — no application code was written as part
of this decision update.

### #3 — Closed expense vocabulary — APPROVED AS WRITTEN, 2026-08-04

The blueprint's draft candidate list (Part 1.5) is adopted verbatim:
`fuel · reefer_fuel · def · meals · oil_additives · parts_maintenance ·
truck_wash · parking · tolls · scale_tickets · permits_fees · supplies ·
misc`. Recorded via direct instruction in this session, 2026-08-04.

**Unblocked:** `contracts/expense_vocabulary.schema.json` frozen v1.0;
Library copy at `library_seed/Vocabulary/expense_vocabulary.v1.json`.
ExpenseRecord category validation and Lane D's Expense Summary
template/filter/fixtures are now authorized but not built.

### #4 — Hard approval gates — APPROVED AS WRITTEN, 2026-08-04

The blueprint's draft seven-gate list (Part 2.1) is adopted verbatim:
government filings, accounting writes, binding external communications,
Library truth demotion, constitution amendments, worker commissioning,
silence-is-never-consent. Recorded via direct instruction in this
session, 2026-08-04.

**Unblocked:** `docs/governance/DISPATCH_BASE_CONSTITUTION_v1.md`'s HARD
APPROVAL GATES section is filled and adopted. The first merge into
`integration` (validation gate 6, docs-match-as-built) is cleared for
this reason specifically — no lane build has occurred yet, so no merge is
imminent regardless.

### #14 — Trade Memory doctrine — APPROVED, 2026-08-04

The blueprint's draft Trade Memory rules (Part 2.3) are adopted: physical
home (`OPERATIONS\Workers\<name>\TradeMemory\`), closed entry-type system,
"optimize HOW, never WHETHER" rule, freeze-at-journeyman-certification
semantics, and the promotion path (worker proposes → Librarian routes →
Mike approves → Library). Recorded via direct instruction in this
session, 2026-08-04.

**Unblocked:** `docs/governance/MEMORY_DOCTRINE_v1.md`'s TRADE MEMORY
section is filled and adopted. Per the Hold Re-Entry Protocol, Packet C-3
(Trade Memory) may be issued before any journeyman certification — no
worker has reached journeyman status; nothing is built yet.

## Provenance note on this resolution batch

This session's user message approving #2/#3/#4/#14 referenced "attached
documents" as governing authority, but no separate document was actually
uploaded in that turn. The approval statement was given directly in the
message text (a status line per item: APPROVED / APPROVED AS WRITTEN /
APPROVED). Per `CONSTITUTION.md` Article XII, amendment requires
deliberate human approval — a direct, unambiguous instruction from the
session's principal (jax1313@outlook.com, operating as Mike Zachary's
authority throughout this session) satisfies that. This entry records
that the operative approval text is the chat instruction itself, dated
2026-08-04, not a separate file this repository can point to.

## Open

(none — all four originally-held items are resolved as of 2026-08-04)

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

### Lane A merge approval — APPROVED, 2026-08-04

Per Hard Approval Gate #7 (`DISPATCH_BASE_CONSTITUTION_v1`: "Approval is
an affirmative act recorded in the decision queue. Silence, timeout, or
absence is never consent."): Mike reviewed the Lane A human walkthrough
(`docs/lanes/A/WALKTHROUGH_REPORT_v1.md` — register/retrieve/hash-verify
plus a tamper-detection check, run against a throwaway sandbox) and
approved it in the same message that also instructed the merge into
`integration` ("yes go ahead and also merge"). This is the affirmative act
`DISPATCH_BUILD_BLUEPRINT_v1` Part 5 gate 5 requires before any lane merge
— the walkthrough report itself was evidence for this decision, not a
substitute for it.

Mike also instructed, in the same message, that all future lane
walkthroughs (B, C, D) follow the same procedure Lane A used. That
standing procedure is now recorded at
`docs/reference/WALKTHROUGH_PROCEDURE_v1.md`.

**Unblocked:** `build/librarian-spine` merges into `integration` — Lane A
is Group 1's first merge, per `DISPATCH_BUILD_BLUEPRINT_v1` Part 4.5.

### Lane B merge approval — APPROVED, 2026-08-04

Per Hard Approval Gate #7: Mike reviewed the Lane B human walkthrough
(`docs/lanes/B/WALKTHROUGH_REPORT_v1.md` — approve one item, reject one
item, plus a bonus check that an already-decided item refuses a second
decision, run against the real Flask dev server per
`docs/reference/WALKTHROUGH_PROCEDURE_v1.md`) and, when asked whether he
was satisfied and wanted it merged, replied "merge" — a direct,
affirmative instruction responding to that specific question, not silence
or a timeout. This is the affirmative act gate 5 requires; the walkthrough
report was evidence for the decision, not a substitute for it.

**Unblocked:** `build/manager-queue` merges into `integration` — Lane B is
Group 1's second merge, per `DISPATCH_BUILD_BLUEPRINT_v1` Part 4.5
(after Lane A).

### Lane C merge approval — APPROVED, 2026-08-04

Per Hard Approval Gate #7: Mike reviewed the Lane C human walkthrough
(`docs/lanes/C/WALKTHROUGH_REPORT_v1.md` — intake through routing and
quarantine both, a live reefer-safety refusal check, a draft IFTA
worksheet from fixture rate data with all ten exception detectors run,
and a full submit → approve → seal cycle with the sealed bundle
confirmed on disk) and, when asked whether he was satisfied and wanted it
merged, replied "yes continue" — a direct, affirmative instruction
responding to that specific question, not silence or a timeout. This is
the affirmative act gate 5 requires; the walkthrough report was evidence
for the decision, not a substitute for it.

**Unblocked:** `build/receipt-ifta` merges into `integration` — Lane C is
Group 1's third merge, per `DISPATCH_BUILD_BLUEPRINT_v1` Part 4.5 (after
Lanes A and B).

### Lane D merge approval — APPROVED, 2026-08-04

Per Hard Approval Gate #7: Mike reviewed the Lane D human walkthrough
(`docs/lanes/D/WALKTHROUGH_REPORT_v1.md` — a real fuel purchase through
Lane C's intake pipeline and a real IFTA worksheet via `WorksheetEngine`,
then "fuel today" answered in one glance, IFTA Position reading the
stored worksheet exactly, a save-for-print round trip with the archive
copy independently confirmed on disk, a malformed-CSV quarantine, a
no-worksheet "no data" page, and a direct raw-SQL `DELETE` against
`print_queue` rejected by the trigger itself, all run against the real
Flask dev server per `docs/reference/WALKTHROUGH_PROCEDURE_v1.md`) and,
when asked whether he was satisfied and wanted it merged, replied "yes,
go ahead and merge" — a direct, affirmative instruction responding to
that specific question, not silence or a timeout. This is the
affirmative act gate 5 requires; the walkthrough report was evidence for
the decision, not a substitute for it.

**Unblocked:** `build/reports` merges into `integration` — Lane D is
Group 1's fourth and last merge, per `DISPATCH_BUILD_BLUEPRINT_v1` Part
4.5 (after Lanes A, B, and C).

### Lane D deferred fidelity gate — CLOSED, 2026-08-04

Per Mike's direct instruction ("Run the deferred fidelity gate against
integration's real data"), `REPORTS_CHARTER_v1.md`'s deferred gate — every
displayed total equals independent SQL arithmetic, re-run against real
Lane C output on `integration` — was run against `integration` @
`44493fe`. A 3-jurisdiction/2-fuel-type/6-category dataset was built
through the real intake pipeline and `WorksheetEngine`; 33/33 independent
checks passed, including IFTA's fleet_mpg/net_tax re-derived from raw
tables per computation spec 3.5, not just compared to the stored
worksheet. Full detail: `docs/lanes/D/FIDELITY_GATE_REPORT_v1.md`. The
strongest checks are now a permanent regression
(`tests/lane_d/test_fidelity_gate.py`). This closes the last open item
from Lane D's launch package and merge.

### Evidence Record contract amendment (v1.0 -> v1.1) — APPROVED, 2026-08-04

While designing the DispatchPilot input workflow (six-folder manual-drop
pilot: `Inbox, Fuel, Receipts, RateCons, POD, ELD, Misc`), the build
session found that `evidence_record.schema.json`'s `document_type` enum
had no value for a rate confirmation, a proof of delivery, or ELD export
data — those document types can't be registered as governed evidence at
all today. Two resolutions were proposed: (1) extend the enum
additively, so every document type gets the same real, hash-verified,
audited evidence-registration path; or (2) give unrecognized types a
separate, lower-trust logging path outside the Evidence Spine. Mike
approved option 1 explicitly, and explicitly rejected option 2 in the
same message: "Do NOT create a secondary evidence path. Do NOT create a
reduced-trust evidence path. Do NOT bypass the Evidence Spine. The
Evidence Spine remains the single governed evidence system."

**Evidence First Doctrine, adopted as of this decision:** if a document
is a legitimate business artifact, it belongs in the Evidence Spine.
Processing capability does not determine whether something is evidence —
a fuel receipt, a rate confirmation, a proof of delivery, an ELD export,
an invoice, a maintenance record, and a compliance record are all
evidence, whether or not this system yet knows how to extract or route
what's inside them. Not being able to process a document's contents yet
is never a reason to register it any less rigorously than one this
system already understands.

**Amendment, additive only:** `document_type` gains `rate_confirmation`,
`proof_of_delivery`, `eld_export`, and `unclassified` (the honest label
for a real file that matches none of the known types — never a guess at
one of the others). No existing value renamed, removed, or reinterpreted;
no other field changed. Contract bumped `FROZEN v1.0` → `FROZEN v1.1`;
`src/dispatch/evidence/interface.py`'s `VALID_DOCUMENT_TYPES` and
`SCHEMA_VERSION` updated to match in the same change, per
`contracts/CONTRACT_REGISTER.md`'s rule that a frozen contract changes
"only by Mike's decision, a version bump, and same-day notice to every
open lane." No lane branch was open at the time (Group 1 fully merged
into `integration` already), so there was no open lane to notify.

**Unblocked:** the DispatchPilot input workflow may register every
document type it needs (Fuel, Receipts, RateCons, POD, ELD, Misc) through
the single, real `EvidenceSpine.register()` — no secondary path.

## Open

(none — all four originally-held items, the Lane A, Lane B, Lane C, and
Lane D merge approvals, the Lane D deferred fidelity gate, and the
Evidence Record v1.1 amendment above, are resolved as of 2026-08-04)

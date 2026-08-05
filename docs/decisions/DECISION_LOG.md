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

### Dispatch Shell merge approval — APPROVED, 2026-08-04

Per Hard Approval Gate #7: Mike reviewed the Dispatch Shell human
walkthrough (`docs/website/WALKTHROUGH_REPORT_v1.md` — a fresh install
with no crash, a real success and a real failure on the same Process
Inbox run, a real link generated by Queue's own unmodified template
followed and resolved, Reports reflecting exactly what routed, and every
claim independently re-verified against the raw database and filesystem)
and, when asked whether he was satisfied and wanted it merged, replied
"yes, go ahead and merge" — a direct, affirmative instruction responding
to that specific question, not silence or a timeout. This is the
affirmative act gate 5 requires; the walkthrough report was evidence for
the decision, not a substitute for it.

**Unblocked:** `build/dispatch-shell` merges into `integration` — Mike's
one bookmark: `/` (dashboard), `/queue` and `/reports` (mounted,
unmodified), and `/pilot` (new, with the real Process Inbox button).

### WorksheetEngine Preview Mode merge approval — APPROVED, 2026-08-04

Preview Mode itself was approved in principle earlier the same day,
against `docs/ifta-clerk/IFTA_CLERK_BLUEPRINT_v1.md` section 6.1, under
six explicit conditions: no database writes, no worksheet IDs, no audit
status changes, no approval path activation, clearly labeled PREVIEW,
cannot be mistaken for a filed worksheet. Per Hard Approval Gate #7, Mike
reviewed the walkthrough
(`docs/ifta-clerk/WORKSHEET_PREVIEW_MODE_WALKTHROUGH_REPORT_v1.md` — a
genuinely fresh database producing a clean error instead of a crash, real
data seeded through real entry points, `preview()`'s output independently
verified by hand and matched exactly, both designed failure paths fired
for real, and a real `build()` run for direct comparison confirming
identical numbers and zero rows left behind by `preview()` before or
after) and, when asked whether he was satisfied and wanted it merged,
replied "yes, go ahead and merge" — a direct, affirmative instruction
responding to that specific question, not silence or a timeout.

**Unblocked:** `build/ifta-worksheet-preview` merges into `integration` —
`dispatch.ifta.worksheet.preview()`, a live, non-persisting estimate
sharing computation spec 3.5's arithmetic with `build()` via new
module-level `_aggregate_mileage`/`_aggregate_fuel`/
`_compute_worksheet_lines` helpers. As a direct consequence of that
refactor, `build()` also stopped crashing with a raw
`sqlite3.OperationalError` on a genuinely fresh database — the bug class
`docs/ifta-ui/NOTES.md` (unmerged `build/ifta-ui` branch) already flagged
as needing a dedicated fix in `worksheet.py` itself.

### Category 2 Live Indicators merge approval — APPROVED, 2026-08-04

Building on Preview Mode's approval earlier the same day, Mike approved
Live Indicators in principle against `docs/ifta-clerk/IFTA_CLERK_BLUEPRINT_v1.md`
section 8, directing: proceed with 4 of the 5 originally-scoped
worksheet-free detectors, add severity classification, document
explicitly that Live Indicators remain informational only with no
workflow side effects, and maintain the same five structural protections
as Preview Mode. Two scope questions were raised directly during design
rather than assumed: whether to fold in the 5 worksheet-dependent
detectors now that `preview()` exists (Mike: no, keep this build at the
original scope, treat that as a separate follow-on), and how to handle
`broken_evidence_linkage` — found during design to write a real
`audit_log` row on every call via `EvidenceSpine.retrieve()`, and a real
urgent Queue item on a hash mismatch (Mike: exclude it from this build).

Per Hard Approval Gate #7, Mike reviewed the walkthrough
(`docs/ifta-clerk/LIVE_INDICATORS_WALKTHROUGH_REPORT_v1.md` — a
genuinely fresh database producing empty findings instead of a crash,
real fuel data through the real CSV intake pipeline producing a real
odometer discontinuity, `audit_log`'s pre-existing count isolated
precisely and confirmed unchanged across repeated calls, a real
reefer-flagged row and a real sealed-quarter straggler both firing
correctly with their documented severities, and a cross-check against
each detector called individually matching exactly) and, when asked
whether he was satisfied and wanted it merged, replied "yes, go ahead and
merge" — a direct, affirmative instruction responding to that specific
question, not silence or a timeout.

**Unblocked:** `build/ifta-live-indicators` merges into `integration` —
`dispatch.ifta.live_indicators.live_indicators()`, calling
`odometer_discontinuity`, `active_truck_days_no_mileage`,
`late_arrival_closed_quarter`, and `reefer_in_propulsion` directly,
never through `run_all_detectors()`, each finding labeled with a
severity from its own closed vocabulary
(`critical`/`warning`/`notice`), distinct from Queue's own priority
vocabulary.

### IFTA Clerk Blueprint reconciliation merge approval — APPROVED, 2026-08-04

After both Preview Mode and Category 2 Live Indicators merged, Mike
directed that `docs/ifta-clerk/IFTA_CLERK_BLUEPRINT_v1.md` be reconciled
against what was actually built rather than left describing the original
projection. Amendment 4 was written: sections 3, 6, 6.1, 7, 8, 12, and 13
updated to reflect both features as built (not "approved in principle" /
"recommended"), and two findings the original text didn't anticipate —
Live Indicators shipping at 4 detectors rather than 5
(`broken_evidence_linkage` excluded, found to write a real `audit_log`
row and, on a hash mismatch, a real urgent Queue item, via
`EvidenceSpine.retrieve()`), and folding the five worksheet-dependent
detectors into Category 2 via `preview()` turning out to be its own
explicit decision rather than the automatic unlock §8's original text
described — recorded as two new open questions (§12.7, §12.8) rather
than silently dropped or silently resolved.

Mike replied "Approved. Merge docs/ifta-clerk-blueprint into
integration. The blueprint now accurately reflects implemented behavior.
Keep `broken_evidence_linkage` and worksheet-dependent detector
integration as explicitly deferred open items." — a direct, affirmative
instruction confirming both the reconciliation's accuracy and the merge,
in the same message. Documentation-only change (no code); the same
directness this project has already extended to prior doctrine and
launch-package documents.

**Unblocked:** `docs/ifta-clerk-blueprint` merges into `integration` —
`IFTA_CLERK_BLUEPRINT_v1.md` (Amendment 4),
`docs/governance/OCR_VISION_EXTRACTION_DOCTRINE_v1.md`, and the
blueprint's four prior amendments, all landing in `integration` for the
first time together.

## Open

(none — all four originally-held items, the Lane A, Lane B, Lane C, and
Lane D merge approvals, the Lane D deferred fidelity gate, the Evidence
Record v1.1 amendment, the Dispatch Shell merge approval, the
WorksheetEngine Preview Mode merge approval, the Category 2 Live
Indicators merge approval, and the IFTA Clerk Blueprint reconciliation
merge approval above, are resolved as of 2026-08-04)

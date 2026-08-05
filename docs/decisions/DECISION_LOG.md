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

### Review Dashboard (Phase 3) merge approval — APPROVED, 2026-08-04

Mike directed Phase 3 with new scope: the Review Dashboard becomes the
primary user experience of the IFTA Clerk, while explicitly maintaining
Evidence First, Read-only Workspace, Human Authority, Recommendation
Packages Only, and no QuickBooks/DocuSign/Filing integration. The design
(a new `dispatch.ifta_clerk` app, mounted at `/ifta-clerk`, all seven
`IFTA_CLERK_BLUEPRINT_v1.md` section 7 panels assembled from a single
read-only connection) was brainstormed and approved before any code, per
this project's standing brainstorming requirement. One real finding
surfaced and resolved during design: panel 6 (evidence links) as
originally specced would call `EvidenceSpine.retrieve()` per record,
writing a real `audit_log` row on every dashboard view — the same class
of side effect already ruled out for `broken_evidence_linkage`. Raised
directly; Mike chose a plain-reference read instead.

Per Hard Approval Gate #7, Mike reviewed the walkthrough
(`docs/ifta-clerk/REVIEW_DASHBOARD_WALKTHROUGH_REPORT_v1.md` — Shell's
home page linking to the dashboard first and prominently, a genuinely
fresh install producing a clean empty state, real fuel/mileage/rate data
through real entry points with `fleet_mpg`/`net_tax` verified by hand,
the failure path (a malformed quarter) handled cleanly, Category 1 and
Category 2 exceptions confirmed never conflated, and zero governed side
effects across roughly ten page loads independently confirmed via raw
`sqlite3`) and, when asked whether he was satisfied and wanted it merged,
replied "yes, go ahead and merge" — a direct, affirmative instruction
responding to that specific question, not silence or a timeout.

**Unblocked:** `build/ifta-clerk-review-dashboard` merges into
`integration` — the Review Dashboard, now Mike's primary entry point for
IFTA, mounted at `/ifta-clerk` and linked first from the Shell's home
page.

### Prepare This Quarter / Submit for Approval merge approval — APPROVED, 2026-08-04

Mike directed Phase 5 ("Prepare This Quarter"), modifying the
blueprint's original three-step design ("`build()` +
`run_all_detectors()` + `submit_for_approval()` in sequence"): Prepare
should build the worksheet, run detectors, and assemble the review
package, but must not automatically submit for approval — submission
stays a separate human action, to maintain a clear separation between
Preparation / Review / Approval Routing. Design and this modification
were confirmed before any code, per this project's standing
brainstorming requirement. One design question resolved directly during
that pass: "assemble review package" required no new artifact — the
already-built Review Dashboard already assembles exactly this the
moment a real worksheet exists.

Per Hard Approval Gate #7, Mike reviewed the walkthrough
(`docs/ifta-clerk/PREPARE_THIS_QUARTER_WALKTHROUGH_REPORT_v1.md` — the
failure path covered first with no data at all, real fuel/mileage/rate
data through real entry points with `fleet_mpg` verified by hand, no
auto-submit confirmed via raw `sqlite3` after a real prepare, a real
approval Queue item created on a separate real submit, a double-submit
cleanly refused with the count staying at one, and the real,
unmodified `/queue/` app independently confirming the created item) and,
when asked whether he was satisfied and wanted it merged, replied "yes,
go ahead and merge" — a direct, affirmative instruction responding to
that specific question, not silence or a timeout.

**Unblocked:** `build/ifta-clerk-prepare-quarter` merges into
`integration` — `dispatch.ifta_clerk.prepare`'s two write actions,
`prepare_quarter()` and `submit_quarter_for_approval()`, kept
structurally separate from each other and from `attempt_seal()`
(unreachable from this app entirely), each proven by `ast`-parsed
imports and function-source scans, not just asserted.

### Recommended Payment Amount merge approval — APPROVED, 2026-08-05

Mike directed Phase 6 (Recommendation Package generation) as item 2 of
a five-item work list. Which of the three named package types to build
first (a prepared DocuSign package, a drafted accounting notification,
a recommended payment amount) was left unanswered when asked; the build
session proceeded with its own stated recommendation — payment amount
first, since it has zero external-system dependency, unlike the other
two which would need a real DocuSign or accounting-system schema this
codebase has never integrated with — flagged explicitly as an
assumption. Mike then approved the presented design directly ("yes
proceed"): applies only to sealed worksheets; computation wraps the
sealed `total_net_tax` in a remit/credit/no_payment_due label; one JSON
file to Archive, no new database table; no payment API, bank
integration, or accounting write anywhere in this codebase.

Per Hard Approval Gate #7, Mike reviewed the walkthrough
(`docs/ifta-clerk/PAYMENT_RECOMMENDATION_WALKTHROUGH_REPORT_v1.md` —
the failure path covered first with no worksheet at all, real
fuel/mileage/rate data spanning two jurisdictions through real entry
points, a full real prepare/submit/approve/seal pipeline producing a
real credit position hand-verified against the generated file, a
repeated request confirming idempotency with an unchanged
`generated_at`, and the real, unmodified `/queue/` app independently
confirming the same approved item) and, when asked whether he was
satisfied and wanted it merged, replied "yes, go ahead and merge" — a
direct, affirmative instruction responding to that specific question,
not silence or a timeout.

**Unblocked:** `build/ifta-clerk-payment-recommendation` merges into
`integration` — `dispatch.ifta_clerk.recommend`'s one write action,
`generate_payment_recommendation()`, structurally incapable of any
database write (its only connection parameter is `read_only_conn`) and
proven, by `ast`-parsed imports, to import nothing with send, approval,
or sealing capability.

### OCR fenced-JSON fix merge approval — APPROVED, 2026-08-05

Mike supplied a real, disposable testing `ANTHROPIC_API_KEY` directly
in-session, unblocking item 4 of his 5-item work list ("OCR validation
with real receipts") for the first time all session. Per standing
practice the key was never written to any file — used only as a
transient environment variable for the lifetime of each live call, then
discarded. A live call against a real (synthesized, since no real
scanned receipt existed in this build environment) pump-receipt image
found a real bug: Claude's real output wraps its JSON object in a
` ```json ... ``` ` markdown fence despite the prompt saying "no other
text," and `_parse_response_text()` in
`src/dispatch/receipt/extraction/vision.py` called `json.loads()`
directly — every real scanned receipt would quarantine
unconditionally, not occasionally. Mike directed the fix, a regression
test using the exact fenced shape from the live call, and the same
branch → test → merge pipeline as everything else this session
("Want me to go ahead and fix `_parse_response_text` ... YES"), then
approved the merge directly ("Merge Yes").

Re-verified live after the fix, not just via the automated suite: the
identical receipt image now routes cleanly to a real
`FuelRecord`/`ExpenseRecord`, every extracted field checked by hand
against the source image (vendor, TX jurisdiction correctly derived
from the address, diesel, 112.4 gallons, $438.24 total, unit number,
driver, odometer, card last-4, receipt number, 0.97 confidence).
`docs/lanes/C/NOTES.md` Session 3 has the full record.

**Unblocked:** `build/ocr-fenced-json-fix` merges into `integration` —
`_strip_markdown_fence()` in `dispatch.receipt.extraction.vision`, and
`anthropic>=0.40` uncommented in `requirements.txt` now that its own
stated condition (a real key supplied, extraction exercised live) is
true.

### Archive Package evidence-refs merge approval — APPROVED, 2026-08-05

Mike directed item 3 of his 5-item work list ("Archive Package
generation"). No blueprint document defines "Archive Package" for IFTA
specifically; investigation found `dispatch.ifta.package.attempt_seal()`
already writes a sealed bundle to `ARCHIVE\IFTA\<quarter>\<id>.json`
whose own docstring has always promised "worksheet + lines + evidence
refs," but the actual bundle carried no evidence at all —
`ifta_worksheet_lines` were jurisdiction aggregates with nothing linking
a line's numbers back to the mileage/fuel/evidence records that produced
them. Mike confirmed the scope directly ("close the evidence-refs gap")
before any code was written, then approved the presented design
("yes, go ahead and build it").

Refs are captured at `WorksheetEngine.build()` time, not re-derived at
seal time, so they can't drift from what was actually computed if more
data gets entered before approval completes — matching
`ifta_worksheet_lines`'s own documented "computation snapshot,
INSERT-only" doctrine. Live-verified in a throwaway sandbox
(`docs/lanes/C/NOTES.md` Session 4): a real fuel CSV through the real
intake pipeline, a real mileage entry, a real
build/submit/approve/seal pipeline, then the sealed bundle file read
directly off disk and checked by hand — the fuel record's vendor, date,
and gallons matched the source CSV exactly, its linked
`evidence_record`'s `archive_path`/`file_hash` were real resolved
values, and the mileage record's `entered_by`/`miles`/`period` matched
the CLI command exactly. Mike then approved the merge directly ("Merge
Yes").

**Unblocked:** `build/archive-package-evidence-refs` merges into
`integration` — the new `ifta_worksheet_lines.related_record_ids`
column, `_resolve_line_evidence()` in `package.py`, and the
`_aggregate_mileage`/`_aggregate_fuel` provenance capture in
`worksheet.py`, all purely additive to computation spec 3.5's
arithmetic.

### Mileage source strategy / mileage entry UI merge approval — APPROVED, 2026-08-05

Mike directed the last item of his 5-item work list ("mileage source
strategy"). Investigation found the blueprint had already posed this
exact question as an open item (section 12, question 2: "Is manual
entry acceptable as the ongoing source of truth indefinitely?"), and
that ELD integration had already been ruled out explicitly, twice, well
before this session (the original DispatchPilot direction, and blueprint
section 3, unchanged). Mike confirmed the presented design directly
("yes, go ahead and build it"): manual entry stands as the permanent
source of truth; a real entry UI closes the CLI-only gap both pilot
runs flagged; a non-blocking plausibility warning (reusing
`exceptions.DEFAULT_MPG_BAND`, not a new threshold) surfaces at entry
time what `fleet_mpg_out_of_band` would otherwise only catch after a
full worksheet build — directly targeting the risk both pilot runs
independently observed twice.

Live-verified against the real running server
(`docs/ifta-clerk/MILEAGE_ENTRY_NOTES_v1.md`): the failure path with
every field missing, a real fuel CSV through the real intake pipeline,
a real mileage entry that triggers the warning and is confirmed written
anyway (never refused) via raw `sqlite3`, and a second real entry in a
fresh quarter confirmed to produce no warning at all. Mike then approved
the merge directly ("Merge Yes").

**Unblocked:** `build/mileage-entry-ui` merges into `integration` —
`dispatch.ifta.mileage.record_mileage()` (moved out of
`tools/mileage_worksheet.py` so the CLI and the UI share one write
path), `worksheet.live_fleet_mpg_estimate()`, and
`POST /record-mileage`, the app's fourth write-capable route. This
closes all five items of Mike's original work list.

### IFTA Clerk Blueprint Amendment 5 reconciliation merge approval — APPROVED, 2026-08-05

Mike directed reconciling the blueprint against everything built this
session. Amendment 5 updates sections 3, 4, 7, 9, 11, 12, and 13 to
match reality: the Review Dashboard (Phase 3) now the app's actual
primary screen, not a design; Prepare This Quarter (Phase 5) built with
its approved modification (submission stays separate) preserved in the
roadmap text, not just the build notes; a new, previously-unnumbered
Phase 5.5 for the mileage entry UI; Phase 6 updated from "future, named
only" to "in progress — one of three types built" (Recommended Payment
Amount); the Archive Package evidence-refs gap closed; vision
extraction's status corrected to "exercised live once, real bug found
and fixed" — explicitly distinguished from §9's formal, still-undone
Stage 1 trial, not overclaimed as satisfying it; and open questions 1
(quarter-end trigger) and 2 (mileage's future) closed, with question 6
(API key ownership) updated but left open since a disposable testing
key doesn't satisfy a standing production credential. One pre-existing
cross-reference error (§6 mislabeling the Prepare This Quarter trigger
"Phase 3" instead of "Phase 5") was fixed in passing. Mike reviewed the
summary and approved the merge directly ("yes, go ahead and merge").

**Unblocked:** `docs/ifta-clerk-blueprint-amendment-5` merges into
`integration` — documentation only, no code changes. This is the
blueprint's second reconciliation pass (see the entry above for the
first, Amendment 4).

## Open

(none — all four originally-held items, the Lane A, Lane B, Lane C, and
Lane D merge approvals, the Lane D deferred fidelity gate, the Evidence
Record v1.1 amendment, the Dispatch Shell merge approval, the
WorksheetEngine Preview Mode merge approval, the Category 2 Live
Indicators merge approval, the IFTA Clerk Blueprint Amendment 4
reconciliation merge approval, the Review Dashboard merge approval, the
Prepare This Quarter / Submit for Approval merge approval, the
Recommended Payment Amount merge approval, the OCR fenced-JSON fix merge
approval, the Archive Package evidence-refs merge approval, the mileage
source strategy / mileage entry UI merge approval, and the IFTA Clerk
Blueprint Amendment 5 reconciliation merge approval above, are resolved
as of 2026-08-05)

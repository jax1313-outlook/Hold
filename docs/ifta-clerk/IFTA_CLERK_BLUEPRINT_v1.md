# IFTA_CLERK_BLUEPRINT_v1

Design correction and future build plan. **No code changes accompany
this document.** Written in response to a direct correction of the
`build/ifta-ui` direction (2026-08-04): that package is a real, working
*tool*, but a tool is not what was asked for. This document defines what
was actually asked for — an IFTA *Clerk* — and how Dispatch gets there
without discarding what already exists or overbuilding what doesn't need
to exist yet.

**Amendment 1 (2026-08-04):** aligned with
`docs/governance/OCR_VISION_EXTRACTION_DOCTRINE_v1.md`: §4's workflow
table reordered and gained an explicit Validation Layer stage.

**Amendment 2 (2026-08-04):** direction and the OCR/Vision Doctrine
approved; the workspace question (§5) resolved — read-only, assembled
from existing sources, no duplicate stores, no new workspace records.
Four sections added at direction: Quarter Accumulation Model (§6),
Exception Dashboard (§8, split out from the Review Dashboard), and OCR
Operational Validation Plan (§9). The Review Dashboard (§7) is expanded.
Phase 4 language tightened to "recommendation packages only."

**Amendment 3 (2026-08-04):** the `WorksheetEngine` preview-mode
extension (§6.1, §12.5) approved in principle, subject to six explicit
conditions (no database writes, no worksheet IDs, no audit status
changes, no approval path activation, clearly labeled PREVIEW, cannot be
mistaken for a filed worksheet). §6.1 specifies how each is satisfied by
construction. This is design approval — the code change itself still
requires its own launch package before it's written.

**Amendment 4 (2026-08-04):** reconciles this document against two
things actually built and merged since Amendment 3, and two findings
made during that work that this document did not anticipate.
`dispatch.ifta.worksheet.preview()` (§6.1, §12.5) is built, tested,
walked through, and merged — no longer a design pending
implementation; see `docs/ifta-clerk/WORKSHEET_PREVIEW_MODE_NOTES_v1.md`
and `WORKSHEET_PREVIEW_MODE_WALKTHROUGH_REPORT_v1.md`. Category 2 Live
Indicators (§8, Phase 2) is also built and merged, but at a **corrected
scope of 4 detectors, not 5**: `broken_evidence_linkage`, found during
design to call `EvidenceSpine.retrieve()` — which writes a real
`audit_log` row on every call and, on a hash mismatch, a real urgent
Queue item — was excluded rather than accepted as "live," since that's
exactly the kind of dashboard-viewing side effect Category 2 exists to
rule out. Separately, folding the five worksheet-dependent detectors into
Category 2 via `preview()` — which §8's original text treated as an
automatic unlock once preview mode existed — was, when preview mode
actually landed, treated as its own explicit decision rather than
automatic, and deferred. See
`docs/ifta-clerk/LIVE_INDICATORS_NOTES_v1.md` and
`LIVE_INDICATORS_WALKTHROUGH_REPORT_v1.md`. §3, §6, §6.1, §7, §8, §12,
and §13 are updated below to match reality as built, not as originally
projected.

**Amendment 5 (2026-08-05):** reconciles this document against five
more real branches built and merged since Amendment 4, all against
`integration`: the Review Dashboard (§7, Phase 3) — no longer a design,
the app's actual primary screen, mounted at `/ifta-clerk`; Prepare This
Quarter (§13, Phase 5) — built with one explicit correction to this
document's own projected text, given directly by Mike before any code
was written: submission stays a separate, deliberate human action,
never bundled into preparation; Recommended Payment Amount — the first
of Phase 6's three named recommendation package types, no longer
"future, named only"; a real gap closed in `attempt_seal()`'s sealed
bundle, which §4's stage 10 and this document's own package-builder
description have always said carries "evidence refs" but, until this
session, never actually did; a real bug found and fixed in vision
extraction (§9) via this session's first-ever live call against a real
`ANTHROPIC_API_KEY` — Claude reads a real receipt image correctly, but
wraps its JSON in a markdown fence the extraction code didn't handle,
so every real scanned receipt would have quarantined unconditionally
until fixed; and §12's mileage question (open question 2) resolved —
manual entry, permanently, no ELD/GPS integration ever, with a real
entry UI closing the operational gap both pilot runs independently
found. See `docs/ifta-clerk/REVIEW_DASHBOARD_NOTES_v1.md`,
`PREPARE_THIS_QUARTER_NOTES_v1.md`, `PAYMENT_RECOMMENDATION_NOTES_v1.md`,
`MILEAGE_ENTRY_NOTES_v1.md`, `docs/lanes/C/NOTES.md` (Sessions 3-4), and
`docs/decisions/DECISION_LOG.md` for the full build record and every
merge approval. §3, §4, §7, §9, §11, §12, and §13 are updated below.

## 1. Executive Summary — IFTA Tool vs. IFTA Clerk

**An IFTA Tool** moves Mike's existing clerical work from a terminal
into a browser. He still types mileage in himself. He still copies rate
numbers off a chart himself. He still clicks Build, then Submit, then
Seal, one at a time, for every quarter, forever. The system got a UI;
Mike is still the clerk. `build/ifta-ui` is exactly this, built well,
and it is not the goal.

**An IFTA Clerk** does the clerical work. It watches evidence arrive
(the same intake surface Dispatch already has), reads what's on each
document, files it, keeps a running tally of miles and fuel by
jurisdiction all quarter long, and near quarter-end assembles everything
into one thing: a decision. Mike's job shrinks from *performing* the
quarter's bookkeeping to *reviewing and authorizing* its output. The
system still can't file, pay, or correspond with a tax authority — that
boundary doesn't move — but everything upstream of the human decision
should require no clerical labor from him at all.

The difference is not cosmetic. It's *who does the keystrokes*: today,
Mike (or a person impersonating Mike in testing) performs every step by
hand. In the target state, the system performs every step by hand, and
Mike performs one review.

## 2. Current State vs. Target State

| Step | Current (IFTA Tool, `build/ifta-ui`) | Target (IFTA Clerk) |
|---|---|---|
| Fuel evidence arrives | Mike drops a file; a CSV auto-routes, an image/PDF needs live vision credentials that don't exist yet in this environment | Same intake surface; vision extraction actually configured and exercised, so a photographed receipt becomes a real `FuelRecord` without anyone re-typing it |
| Mileage | Mike types it into a form, one entry at a time | Still Mike's input, permanently, by deliberate decision, not a gap (§3, §12.2, resolved 2026-08-05) — but the *form* is now the Clerk's own (`/record-mileage`), with a live plausibility check, so entry becomes a small, occasional task, not a session |
| Rates | Mike types a new rate row into a form | Unchanged — rate entry is inherently a human-transcribes-a-published-number task; this was never clerical busywork the Clerk should absorb |
| "Is the quarter ready?" | Mike has to think to ask this — nothing tells him | The Clerk knows continuously: how much data exists, what's missing, what's flagged, what's uncertain |
| Build the worksheet | Mike clicks Build | The Clerk prepares the draft itself, at or near quarter-end, without being clicked into it line by line |
| Review | Mike reads a worksheet detail page he had to navigate to | Mike is handed one decision package: numbers, exceptions, missing data, evidence links, confidence — everything needed to say yes or no, nothing he has to go hunting for |
| Approve | Mike clicks Approve in the Queue | Unchanged — this is correctly a human gate already |
| Seal | Mike clicks Seal | The Clerk seals once approval exists — Mike doesn't have to remember to come back and click a third button |
| After sealing | Nothing | A DocuSign package, an accounting notification, and a recommended payment amount, each a **proposal only** — see §11. The payment amount is built (2026-08-05); the other two remain future |

## 3. What Already Exists That the Clerk Can Be Built On

Stated honestly — some of this is fully proven, some is real but
unexercised, and two pieces are genuine, unsolved gaps.

- **Evidence Spine (Lane A).** No change needed. Already accepts any
  document type after the v1.1 amendment (`rate_confirmation`,
  `proof_of_delivery`, `eld_export`, `unclassified` alongside the
  original six) — real, hash-verified, audited, regardless of whether
  Dispatch can yet act on a document's contents.
- **DispatchPilot Inbox (already built).** The intake surface the Clerk
  needs already exists. `process_inbox()` is explicitly designed as "no
  daemon — an external trigger calls this." The Clerk doesn't need a new
  intake mechanism; it needs this one called on a cadence instead of
  only on a manual click. *Standing up that cadence is infrastructure
  (a scheduler) and is explicitly out of this blueprint's scope* (§11) —
  named here as a real prerequisite, not solved by this document.
- **Vision extraction (`dispatch.receipt.extraction.vision`) — exercised
  live once, 2026-08-05, real bug found and fixed.** For the first time
  in this project, a real (disposable, testing-only) `ANTHROPIC_API_KEY`
  was supplied and a real call made against a real receipt image. The
  extraction itself works well — every field read correctly,
  `extraction_confidence 0.97` — but the model wraps its JSON output in
  a markdown fence despite the prompt saying "no other text," and
  `_parse_response_text()` called `json.loads()` directly, so the
  document quarantined anyway; **every real scanned receipt would have
  quarantined unconditionally**, not occasionally. Fixed
  (`_strip_markdown_fence()`), re-verified live after the fix — the
  identical image now routes cleanly to a real `FuelRecord`. See
  `docs/lanes/C/NOTES.md` Session 3. This is real signal the extraction
  path works end to end, but **not** §9's formal Stage 1 trial: one
  call, a synthesized image (not an actual photograph or scan), not the
  5-10-real-receipt sample §9 describes, and the testing key used was
  disposable, not a standing credential in a real deployment
  environment. §9 is updated to reflect exactly this much progress, no
  more. See `docs/governance/OCR_VISION_EXTRACTION_DOCTRINE_v1.md` for
  the full architectural doctrine this system already follows for
  extraction.
- **Router (Lane C).** Already creates real `FuelRecord`/`ExpenseRecord`
  rows automatically the moment extraction succeeds, CSV or vision alike
  — no new logic needed for "store extracted data automatically."
- **Mileage — resolved, 2026-08-05: manual entry, permanently.** Closes
  open question 2 (§12). Every jurisdiction-mile entered into this
  system, in every walkthrough and every pilot run, has been typed in
  by a human — and that stays true by deliberate decision, not by
  default. There is no ELD/GPS/odometer-device integration anywhere in
  this codebase and none is planned; this was already decided twice
  before this resolution (the original DispatchPilot direction, and
  this section, unchanged, for a full session) and is now a standing
  answer, not an open question. What changed is entirely operational:
  `POST /record-mileage` (`dispatch.ifta_clerk`) gives mileage entry a
  real front door instead of a CLI-only tool, and
  `worksheet.live_fleet_mpg_estimate()` surfaces a non-blocking
  plausibility warning at entry time — the same `DEFAULT_MPG_BAND`
  `fleet_mpg_out_of_band` already checks, just earlier, closing the
  real operational risk both `docs/pilot/DISPATCH_PILOT_RUN_1_REPORT_v1.md`
  and `RUN_2` independently found ("manual mileage entry is this
  system's one input with no independent cross-check"). See
  `docs/ifta-clerk/MILEAGE_ENTRY_NOTES_v1.md`. The Clerk still cannot
  manufacture mileage data that doesn't exist — it can only make
  entering real data, and catching likely mistakes in it, faster.
- **Exception detectors (Lane C, `exceptions.py`) — ten total, and they
  split cleanly into two groups that matter a great deal for §6 and §8:**
  five (`odometer_discontinuity`, `active_truck_days_no_mileage`,
  `broken_evidence_linkage`, `late_arrival_closed_quarter`,
  `reefer_in_propulsion`) take only a read-only connection and a date
  range — **no worksheet required, real-time, any time**, by function
  signature. This split is verified directly against `exceptions.py`'s
  real function signatures, not assumed. **Signature eligibility is not
  the same as safe-to-call-repeatedly-with-no-side-effects, though** —
  building §8's actual live dashboard (`dispatch.ifta.live_indicators`,
  merged 2026-08-04) found that `broken_evidence_linkage` specifically
  calls `EvidenceSpine.retrieve()`, which always writes a real
  `audit_log` row and, on a hash mismatch, a real urgent Queue item — a
  side effect from merely viewing a dashboard. It was excluded from the
  live module on that basis; see §8. The other four
  (`odometer_discontinuity`, `active_truck_days_no_mileage`,
  `late_arrival_closed_quarter`, `reefer_in_propulsion`) are genuinely
  side-effect-free and are the ones actually live today. The remaining
  five (`fuel_no_miles`, `miles_no_fuel_gap`, `fleet_mpg_out_of_band`,
  `rate_version_mismatch`, `corner_clipping`) take a built worksheet
  dict — they are inherently scoped to a computed aggregate (fleet MPG,
  taxable gallons) that doesn't exist until a worksheet does.
- **Worksheet engine, package builder (Lane C).** `WorksheetEngine.build()`,
  `submit_for_approval()`, `attempt_seal()` are real, tested, and already
  enforce every relevant rule (no fabricated rate, no seal before
  approval, draft-only until sealed). The Clerk calls these same
  functions — it does not need new ones. What changes is *what calls
  them and when* (§10). `WorksheetEngine`'s module also now includes
  `preview()` (§6.1), built and merged 2026-08-04 — the identical spec
  3.5 arithmetic, computed on demand, never persisted — and, since
  2026-08-05, `live_fleet_mpg_estimate()`, the same arithmetic again,
  deliberately independent of any rate table, backing the mileage-entry
  plausibility check above. `attempt_seal()`'s sealed bundle also
  genuinely carries the "evidence refs" its own docstring has always
  promised, as of 2026-08-05 — previously true in name only; see §4,
  row 10, and `docs/lanes/C/NOTES.md` Session 4.
- **Queue (Lane B).** Already the correct, only approval mechanism.
  Proven live twice now (two real pilot runs) that an IFTA approval item
  can be found and decided through the real Queue UI. Unchanged by this
  blueprint.
- **Reports (Lane D).** The IFTA Position report is already close in
  spirit to a "readiness" view — it already reads `fleet_mpg`/`net_tax`
  exactly as stored, already shows exception counts. It needs
  *extending* into a genuine decision package (evidence links,
  confidence, missing-data callouts), not replacing.

## 4. The Target Workflow, Mapped Against What's Built

Evidence is registered *before* extraction, not after, and validation is
its own named stage between extraction and record creation — both
already true of the real, built pipeline.

| Stage | Status |
|---|---|
| 1. Evidence Spine (document arrives, hashed, audited, archived) | Built, proven, unchanged |
| 2. OCR / Vision Extraction | Code built; **exercised live once, 2026-08-05 — real bug found and fixed; not yet the formal Stage 1 trial** (§3, §9) |
| 3. Validation Layer | Built (`validators.py` — structural, sum, confidence, dedup), unchanged |
| 4. Fuel + Expense record creation | Built (Router), unchanged |
| 5. Mileage / jurisdiction accumulation | Fuel side built; **mileage source resolved 2026-08-05 — manual, permanently, with a real entry UI and plausibility check** (§3, §12.2, closed) |
| 6. IFTA workspace | **Resolved — read-only, §5** |
| 7. Exception queue | Built (ten detectors + real Queue items); **live-preview split built in §8 — 4 of 10 detectors live today, see amendment 4** |
| 8. Review dashboard | **Built and merged, 2026-08-05 — the app's primary screen, `dispatch.ifta_clerk` at `/ifta-clerk`** (§7) |
| 9. Mike approval | Built, proven live twice, unchanged |
| 10. IFTA package | Built (`attempt_seal`'s bundle); **now genuinely carries evidence refs, 2026-08-05 — previously promised in its own docstring but not implemented** (§3) |
| 11. Archive | Built, unchanged |
| 12. DocuSign / accounting handoff | **One of three named types built, 2026-08-05 — Recommended Payment Amount; the other two remain future, recommendation packages only** (§11, §13 Phase 6) |

## 5. The IFTA Workspace — Resolved

**Confirmed 2026-08-04: read-only. No duplicate stores. No new
workspace records.** `fuel_records`, `expense_records`, and
`mileage_records` already *are* the accumulation — every fuel purchase
and every mileage entry is already sitting in governed tables from the
moment it's recorded, all quarter long. The workspace is not a place
data sits before becoming real; it is a live *view* assembled from where
real data already is. This is a Reports-shaped problem — arithmetic and
grouping over existing records, no domain judgment, no recomputation of
anything Lane C already computes — and fits inside
`REPORTS_CHARTER_v1.md`'s existing bright lines without a new contract.

The workspace *is* the Review Dashboard (§7). What follows in §6 and §8
is the harder question this resolution immediately raises: a live view
needs something to compute against, and the real worksheet-building
machinery (§3) both computes *and persists*. Reconciling "read-only,
assembled from existing sources" with "the real numbers come from a
function that writes to the database" is the actual design problem the
rest of this document works through.

## 6. Quarter Accumulation Model

This is the mechanism question §5 leaves open: **how does a live,
read-only view get numbers that today only exist by calling a function
that persists a real, permanent worksheet row?**

**The tension, stated plainly.** `WorksheetEngine.build()` is the only
code that computes `fleet_mpg`, `taxable_gallons`, and `net_tax` (spec
3.5). It also unconditionally `INSERT`s into `ifta_worksheets` and
`ifta_worksheet_lines` every time it's called — there is no
non-persisting mode today. If the Review Dashboard called `build()`
every time Mike opened it mid-quarter just to show a current estimate,
every page view would create a new, permanent draft worksheet row for
the same quarter — duplicate real records for a value that was only ever
meant to be a glance. That's not a workspace; that's exactly the
"duplicate store" this direction just ruled out, produced by accident
through the one function that happens to compute the numbers.

**Three distinct moments, not one, need to be named separately:**

1. **Continuous accumulation — already happens, no new mechanism.** Fuel
   and mileage records simply grow as intake and entry happen, all
   quarter long. Nothing new here; this is what §5 already resolved.
2. **Live estimate — read-only, computed on demand, never persisted.**
   For the dashboard to show "here's roughly where the quarter stands"
   *before* anyone has decided it's time to build, something has to run
   the spec 3.5 arithmetic without writing anything. **Built and merged
   2026-08-04** — `dispatch.ifta.worksheet.preview()`, see §6.1.
3. **The one real, deliberate Build — persists, exactly as it does
   today.** When Mike (or the Phase 5 "Prepare This Quarter" trigger,
   §13, built and merged 2026-08-05) actually decides the quarter is
   ready, `WorksheetEngine.build()` runs for real, once, producing the
   real draft worksheet, real exceptions, and a real audit trail —
   unchanged from today.

**Closing moment 2 — built, 2026-08-04, per the recommendation below,
implemented as originally proposed.** A module-level `preview()`
function in `worksheet.py` runs the identical spec 3.5 arithmetic and
returns the identical shape of result, skipping the two `INSERT`s — not
a `build(..., persist=False)` flag or a `WorksheetEngine` method as the
two named alternatives suggested, but a standalone function taking only
a read-only connection, so condition 1 (§6.1) is structural rather than
conventional: there is no write-capable connection in scope to
accidentally use. The arithmetic itself
(`_aggregate_mileage`/`_aggregate_fuel`/`_compute_worksheet_lines`) is
now shared between `build()` and `preview()` as module-level functions,
keeping the formula in exactly one place as intended. Went through its
own launch-package-equivalent approval (the six conditions given
directly, §6.1), its own tests, its own live walkthrough, and explicit
merge approval — the same discipline the Evidence Record v1.1 amendment
set as precedent for changing already-merged lane code. See
`docs/ifta-clerk/WORKSHEET_PREVIEW_MODE_NOTES_v1.md` and
`WORKSHEET_PREVIEW_MODE_WALKTHROUGH_REPORT_v1.md`.

**What a live estimate is not.** It is not a second source of truth, not
a competing number, and never appears without a label distinguishing it
from a real worksheet's stored, sealed values. Once a real worksheet
exists for the quarter, the dashboard shows *that* — read exactly as
stored, exactly as Reports' own IFTA Position already does — and the
live-estimate path stops being shown at all for that quarter. There is
never a moment where both a live estimate and a real worksheet's numbers
are on screen at once claiming to answer the same question.

### 6.1 Preview Mode — approved and built, 2026-08-04

Approved in principle subject to six explicit conditions, then built,
tested, walked through, and merged the same day
(`docs/ifta-clerk/WORKSHEET_PREVIEW_MODE_NOTES_v1.md`,
`WORKSHEET_PREVIEW_MODE_WALKTHROUGH_REPORT_v1.md`). Conditions taken
verbatim; each mapped to how the merged code actually satisfies it —
updated below from "will satisfy by construction" to "does satisfy,
verified by both automated tests (`inspect`/`ast`-based, not just
today's return value) and a live walkthrough against a real database":

1. **No database writes.** `preview()` is constructed with only a
   read-only connection — the same `ro_conn` (`readonly.open_read_only()`)
   `WorksheetEngine` already uses for `fuel_records`/`mileage_records`
   today, never the write connection at all. Not "chooses not to write" —
   *has no write-capable connection in scope to write with*, the same
   structural guarantee `readonly.py` already gives every other reader in
   this system.
2. **No worksheet IDs.** No `new_ulid()` call anywhere on this path. The
   returned object has no `ifta_worksheet_id` field — not `None`, not a
   placeholder string, simply absent, so nothing downstream can
   accidentally treat it as a real row's key.
3. **No audit status changes.** No call to `dispatch.common.audit.write_audit_entry()`
   anywhere on this path. A preview computation is not a governed action
   and produces no audit trail entry — silence here is correct, not a
   gap, the same way viewing a report today writes no audit entry.
4. **No approval path activation.** `preview()` never receives or
   constructs a `QueueStore`, never imports `dispatch.ifta.package`, and
   never calls `run_all_detectors()` — the only code that creates Queue
   items. (The five worksheet-scoped exception detectors *could* be
   called directly against `preview()`'s in-memory result the same
   pure-function way the four live worksheet-free ones already are — but
   as of this document's Amendment 4, nothing actually wires that up
   yet; see open question 8, §12.) No code path from `preview()` can
   reach `submit_for_approval()` or `attempt_seal()` either, since both
   require a real `ifta_worksheet_id` to look up a persisted row
   (condition 2 already makes that impossible to supply).
5. **Clearly labeled PREVIEW.** The returned shape carries an explicit
   `"status": "preview"` — a value that never appears in the real
   `ifta_worksheets.status` column (`draft` / `sealed` only, enforced by
   existing schema) — so a preview result and a real row can never be
   confused even if handled generically by the same display code.
6. **Cannot be mistaken for a filed worksheet.** Follows directly from 2,
   3, and 5 together: no ID a real worksheet could have, no audit trail a
   real worksheet would have, and a status value no real worksheet can
   ever carry. The Review Dashboard (§7) additionally renders it under
   distinct language ("Current Estimate," never "Worksheet") wherever it
   appears.

This satisfies all six conditions by construction, not by convention —
each is a structural property of what the function has access to and
what shape it returns, not a rule the code merely promises to follow.

## 7. Review Dashboard — built and merged, 2026-08-05

No longer a design. `dispatch.ifta_clerk`, mounted at `/ifta-clerk`,
linked first and prominently from the Shell's home page — the app's
actual primary screen now, exactly as this document's §1 envisioned.
See `docs/ifta-clerk/REVIEW_DASHBOARD_NOTES_v1.md` and
`REVIEW_DASHBOARD_WALKTHROUGH_REPORT_v1.md`. One screen, one quarter
(and, matching the worksheet engine's own granularity, one fuel type),
assembled entirely from existing sources per §5's resolution. Seven
panels, all built:

1. **Readiness status** — a single rollup label ("ready to prepare" /
   "N exceptions open" / "M records below confidence threshold" /
   "missing mileage for N truck-days"), computed from the panels below,
   still read-only, still no domain judgment — the one genuinely new
   piece of logic on this screen, and a small one.
2. **Miles by jurisdiction** — `mileage_records`, already real. As of
   2026-08-05, this panel also hosts mileage entry itself
   (`POST /record-mileage`) — see §3's mileage resolution and §12.2.
3. **Fuel by jurisdiction** — `fuel_records`, already real (the same
   data Fuel Spend already shows, filtered to the quarter).
4. **Exceptions and missing data** — the full detail is §8; this panel
   is where §8's two categories (confirmed vs. live-preview) actually
   render.
5. **Suspect entries** — `extraction_confidence` already exists on every
   `FuelRecord`/`ExpenseRecord` but isn't surfaced anywhere today. "N
   records below the confidence threshold (§12)" is a small, genuinely
   new, still read-only addition.
6. **Evidence links** — `EvidenceSpine.retrieve()` with hash
   re-verification, the exact pattern Lane B's Queue detail page already
   uses for evidence previews. Reused directly, not reimplemented.
7. **Estimated tax position** — before a real worksheet exists, §6's
   live estimate (`preview()`, §6.1); after one exists, Reports' own
   pattern — `total_net_tax` read exactly as stored, never recomputed.
   Never both at once, per §6. Once a worksheet is **sealed**, this
   panel also shows the real Recommended Payment Amount if one has been
   generated (§13 Phase 6), or a button to generate one — see
   `docs/ifta-clerk/PAYMENT_RECOMMENDATION_NOTES_v1.md`.

All seven fit inside the read-only, no-recomputation boundary Lane D's
charter already established. None of the seven panels themselves
required a new writer; the dashboard's four write actions
(`/prepare`, `/submit`, `/recommend-payment`, `/record-mileage`) are
deliberately separate from `dashboard.py`, which stays exactly as
read-only as originally designed — see §13 Phases 5-6 and the mileage
resolution above.

## 8. Exception Dashboard

Split out from the Review Dashboard because it has a real internal
structure worth making explicit rather than presenting as one
undifferentiated list — conflating these two categories would be exactly
the "Confidently Wrong" failure mode `OCR_VISION_EXTRACTION_DOCTRINE_v1`
warns against, applied to exceptions instead of extraction.

**Category 1 — Confirmed Exceptions.** Real findings from
`ifta_exceptions`, created only when `run_all_detectors()` has actually
run against a real, built worksheet, each already backed by a real Queue
item. These are actionable today, exactly as built — nothing changes
about how they're created; this dashboard only makes them visible
without requiring Mike to open the Queue and read subject lines one at a
time.

**Category 2 — Live Indicators. Built and merged, 2026-08-04, at a
corrected scope of 4 detectors** — `dispatch.ifta.live_indicators.live_indicators()`
(`docs/ifta-clerk/LIVE_INDICATORS_NOTES_v1.md`,
`LIVE_INDICATORS_WALKTHROUGH_REPORT_v1.md`). Of the five worksheet-free
detectors named in §3, four are genuinely pure and side-effect-free —
`odometer_discontinuity`, `active_truck_days_no_mileage`,
`late_arrival_closed_quarter`, `reefer_in_propulsion` — and are called
directly, **without ever calling `run_all_detectors()`**, so nothing is
persisted and no Queue item is created just because Mike opened a
dashboard. Each finding carries a severity (`critical`/`warning`/`notice`,
a closed vocabulary deliberately distinct from Queue's own
`urgent`/`today`/`whenever` priorities, since a live indicator never
touches the Queue).

**`broken_evidence_linkage` was found, during design, not to belong in
this category despite matching its function signature.** It calls
`EvidenceSpine.retrieve()`, which unconditionally writes a real
`audit_log` row every call and, on a hash mismatch, a real urgent Queue
item — a genuine side effect from merely viewing a dashboard, exactly
what Category 2 exists to rule out. It was excluded rather than accepted
silently, and remains available today only through a real
`build()` + `run_all_detectors()`, as a Category 1 (confirmed) exception.
A future retrieve-without-side-effects path could resolve this — named
as an open question, §12.

**§6's preview mode is also now built** (§6.1) — but folding the other
five, worksheet-dependent detectors into Category 2 by computing them
against an in-memory `preview()` result, which this document originally
described as something that "can join this live category too" once
preview mode existed, turned out to be its own explicit decision when
the moment actually arrived, not an automatic unlock: asked directly,
Mike chose to hold Category 2 at its current scope and treat that
folding-in as a separate follow-on. `preview()`'s own failure modes
(`InsufficientDataError`, `MissingRateError`) would also need their own
handling inside a "live" caller before that could safely happen — a real
design question for that follow-on, not resolved here. Named as an open
question, §12.

**The rule that keeps these from ever being confused:** Category 2
findings are never queued, never counted toward "open exceptions" in any
governed sense, and are visually and textually distinct from Category 1
("would flag if built today" vs. "flagged, needs your decision"). A live
indicator disappearing because underlying data changed is normal and
silent; a confirmed exception disappearing requires an actual human
decision through the Queue, exactly as today. This dashboard adds no new
write path — every real exception still only ever comes from the same
real `run_all_detectors()` call it does today.

## 9. OCR Operational Validation Plan

Addressing §3's largest named gap directly: vision extraction is real
code that has never run against a live credential. This is not a build
task this blueprint can close — it's a validation task requiring a real
credential this environment does not have and cannot obtain. What
follows is the plan for when one exists, not an attempt to fake having
run it.

**Prerequisite — partially, informally satisfied, 2026-08-05.** A real
`ANTHROPIC_API_KEY`, supplied by Mike directly in-session — disposable,
testing-only, never written to any file or committed, used only as a
transient environment variable for the lifetime of each live call, then
discarded. This is **not** the standing credential this stage
describes, "configured in whatever real environment eventually runs
this system day to day" — it was a one-session loan that made a first,
informal live trial possible (see below), not a solved prerequisite.
Whoever ends up running this system day to day still needs their own
real, standing key; open question 6 (§12) is informed by this, not
closed by it.

**Stage 1 — Small, supervised extraction trial. Informally, partially
exercised, 2026-08-05 — not yet the formal trial.** One real call
against one synthesized (not photographed or scanned) receipt image:
every field read correctly, `extraction_confidence 0.97`, independently
checked by hand against the source image — but the model's raw output
turned out to need a markdown-fence fix before it could parse at all
(`docs/lanes/C/NOTES.md` Session 3), a real finding this stage's
methodology was built to catch. This is genuine signal the extraction
path works end to end once that fix landed, but it is one call, not the
5-10-image sample this stage specifies, and a synthesized image, not
"an actual photograph or scan" as this paragraph originally
distinguished — that distinction still hasn't been tested. The formal
Stage 1 trial, against real or highly realistic receipt images, one at
a time, remains undone.

**Stage 2 — Confidence calibration. Still not started for real.**
`DEFAULT_CONFIDENCE_THRESHOLD = 0.75` (`validators.py`) was chosen
without ever having a real extraction to calibrate against; one data
point now exists (0.97, correct) from the informal Stage 1 trial above,
but one point is not a calibration set, and it was a synthesized image
besides. Once the formal Stage 1 produces enough real
extraction-confidence values alongside real correct/incorrect outcomes,
check whether 0.75 is actually the right line — a threshold picked
before any live data existed is a placeholder that happens to be
reasonable-sounding, not a validated number. This directly informs §12's
confidence-threshold question and §7's "suspect entries" panel.

**Stage 3 — Real pilot run, vision-enabled.** The same methodology
already twice proven for this project (`docs/pilot/DISPATCH_PILOT_RUN_1_REPORT_v1.md`,
`RUN_2`) — a realistic weekly batch, dropped for real, processed for
real — but this time with actual scanned/photographed receipts and a
real credential, not CSV exports standing in for them. Same standard:
independently re-verify results against the source documents directly,
not just trust the extraction's own confidence score.

**Stage 4 — Rollout gate.** Vision extraction only becomes a *default*
trusted path (rather than "everything quarantines below threshold,
nothing has ever been accepted") once Stage 3's real accuracy rate is
known and acceptable to Mike. No number is proposed here — that's a
decision for whoever reviews Stage 3's actual results, not something
this document should invent in advance of real data.

**What this plan is not.** It is not a claim that vision extraction is
fully validated — 2026-08-05's informal trial is real, positive signal
(and found a real bug the formal trial would also have caught), but one
call against one synthesized image is not Stage 1, let alone Stages 2-4.
The doctrine (§`OCR_VISION_EXTRACTION_DOCTRINE_v1`) this system already
follows for it is sound, verified against real code, and has now been
tested against one real call — Stages 1-4, run formally, are still
ahead.

## 10. What Happens to `build/ifta-ui`

Not defended, not discarded. Its real, tested machinery — `rates.insert_rate()`,
`WorksheetEngine.build()`, `run_all_detectors()`, `submit_for_approval()`,
`attempt_seal()`, and now also `preview()` and `live_indicators()` (§6.1,
§8) — is exactly what the Clerk should call. The mistake
wasn't the underlying calls; it was making *button-clicking through
them* the primary interface. Recommendation: the manual UI remains
useful as a secondary, explicit **override and inspection tool** —
backfilling a missed quarter, correcting something the Clerk flagged,
looking at a worksheet's raw detail — but stops being the thing Mike
uses every quarter. Whether it merges as-is, merges with its role
relabeled, or waits until the Clerk exists is a decision for Mike (§12),
not decided unilaterally here.

## 11. Boundaries (restated as commitments)

- Matrix Group 1's architecture is unchanged. Evidence Spine, Queue, and
  the Receipt→IFTA chain are used as they already exist, not forked or
  duplicated.
- No alternate evidence path, no bypass of Evidence Spine, no bypass of
  Manager Queue approval.
- No live QuickBooks writes, no live DocuSign integration, no real tax
  authority filing, no production infrastructure, no autonomous filing
  or payment — none of this is built now.
- **Future accounting/DocuSign/filing-adjacent work generates
  recommendation packages only** — a proposed payment amount, a prepared
  signature package, a drafted notification — never a live write to
  another system, never an autonomous send. Human authority remains
  final at every one of those steps, the same as it already is for
  approval and sealing today. **Confirmed true under real construction,
  not just promised:** the first type, Recommended Payment Amount,
  built 2026-08-05, writes exactly one proposal file to Archive and
  stops — `generate_payment_recommendation()`'s only connection
  parameter is `read_only_conn`, structurally incapable of any database
  write, and no payment API, bank integration, DocuSign, or QuickBooks
  write exists anywhere in this codebase for it to reach. See §13
  Phase 6.
- Human approval remains required, explicitly, for: IFTA filing,
  DocuSign/signature package, accounting notification, payment/check
  authorization, and sealing (already true — `attempt_seal()` cannot run
  without a real approval, and that doesn't change).
- No new agents are proposed. The Clerk is a workflow — a scheduling and
  presentation change over existing, real functions — not a new
  autonomous decision-maker.

## 12. Open Questions for Mike

1. ~~**Quarter-end trigger**~~ — **APPROVED AND BUILT, 2026-08-05.**
   Manual "Prepare This Quarter" action, exactly the recommended option
   — no scheduler. Built with one modification given directly by Mike
   before any code was written: preparation builds the worksheet and
   runs detectors, but never automatically submits for approval —
   submission stays a separate, deliberate human action, to keep
   Preparation / Review / Approval Routing clearly distinct. See §13
   Phase 5, `docs/ifta-clerk/PREPARE_THIS_QUARTER_NOTES_v1.md`. Closed.
2. ~~**Mileage's future**~~ — **RESOLVED, 2026-08-05: manual entry,
   permanently.** Not a later-phase question — a standing answer. No
   ELD/GPS/odometer-device integration exists or is planned; the
   DispatchPilot `ELD` folder stays evidence-only, with no extraction
   logic, by design. See §3's mileage bullet and
   `docs/ifta-clerk/MILEAGE_ENTRY_NOTES_v1.md`. Closed.
3. **Confidence threshold.** What `extraction_confidence` cutoff should
   route a record to "suspect, review before trusting" rather than being
   silently accepted? §9 recommends calibrating this against real data
   before treating 0.75 as more than a placeholder — but a number still
   needs setting, and that's a decision, not a build task.
4. **`build/ifta-ui`'s fate** (§10): merge as a secondary override tool,
   merge but relabel its role in its own docs, or hold it unmerged
   pending the Clerk's first phase?
5. ~~**`WorksheetEngine` preview-mode extension**~~ — **APPROVED AND
   BUILT, 2026-08-04.** All six conditions satisfied and independently
   verified, both by automated tests and a live walkthrough — see §6.1,
   `docs/ifta-clerk/WORKSHEET_PREVIEW_MODE_NOTES_v1.md`,
   `WORKSHEET_PREVIEW_MODE_WALKTHROUGH_REPORT_v1.md`. Closed.
6. **Who owns Stage 1-4 of §9** — obtaining and holding the real
   `ANTHROPIC_API_KEY`, and where the validation trial actually runs?
   Still open. Mike supplied a disposable, testing-only key directly
   in-session on 2026-08-05, which made an informal, partial Stage 1
   trial possible (§9) and found a real bug — but that key was never
   meant to be, and wasn't treated as, a standing production credential;
   it was used only as a transient environment variable and never
   written to any file. Whoever ends up running this system day to day
   still needs their own real key and their own decision about where
   the formal trial runs. Not resolved by this session's use of one.
7. **`broken_evidence_linkage`'s future path.** It's excluded from
   Category 2 Live Indicators (§8) because `EvidenceSpine.retrieve()`
   always writes an audit entry and can create an urgent Queue item on a
   hash mismatch — a real side effect from viewing a dashboard. Should a
   lighter-weight, genuinely side-effect-free existence-and-hash check be
   built specifically for this live-dashboard use case (duplicating a
   small slice of `retrieve()`'s logic, matching this project's own
   cross-boundary-duplication precedent), or does this detector simply
   stay Category 1-only, confirmed-exceptions-after-a-real-build,
   permanently? Not decided here.
8. **Folding the five worksheet-dependent detectors into Category 2 via
   `preview()`.** §8 originally treated this as automatic once preview
   mode existed; when preview mode actually landed, Mike chose to treat
   it as a separate decision and held Category 2 at 4 detectors. Is this
   worth doing as its own follow-on, and if so, how should `preview()`'s
   `InsufficientDataError`/`MissingRateError` be handled inside a "live,
   never crashes, never queues" caller? Not decided here.

## 13. Phased Build Plan (roadmap, not a launch package)

Each phase is independently shippable and reversible; none commits to
the next.

- **Phase 1 — Surface what already exists.** Expose
  `extraction_confidence` and Category 1 (Confirmed) exceptions in one
  place, read-only. Smallest possible slice, zero new write paths,
  immediately useful regardless of what happens next.
- **Phase 2 — Category 2 Live Indicators. Built and merged, 2026-08-04**
  (§8) — at a corrected scope of 4 detectors, not the 5 originally named:
  `broken_evidence_linkage` was found during design to write a real
  audit entry (and, on a hash mismatch, a real Queue item) on every
  call, and was excluded rather than accepted as side-effect-free. No
  `WorksheetEngine` change was needed for the 4 that shipped — confirmed
  true as built, not just projected.
- **Phase 3 — The Review Dashboard, fully assembled. Built and merged,
  2026-08-05** (§7). All seven panels, real, mounted at `/ifta-clerk`,
  the Shell's primary link. Built before the confidence threshold
  (§12.3) was answered — panel 5 (Suspect entries) uses the existing
  0.75 placeholder, explicitly labeled as such, rather than blocking on
  a still-open question. Mileage's role (§12.2) was still open when this
  phase shipped and was resolved afterward, separately (Phase 5.5,
  below). See `docs/ifta-clerk/REVIEW_DASHBOARD_NOTES_v1.md`,
  `REVIEW_DASHBOARD_WALKTHROUGH_REPORT_v1.md`.
- **Phase 4 — `WorksheetEngine` preview mode. Built and merged,
  2026-08-04** (§6.1, §12.5). Unlocked live tax estimates before a real
  build, exactly as designed. Did **not** automatically unlock the
  remaining five detectors joining Category 2, as originally projected —
  that turned out to be its own explicit decision (open question 8,
  §12), deferred rather than bundled in.
- **Phase 5 — The Clerk's own trigger. Built and merged, 2026-08-05,
  with one correction to this paragraph's original text.** As
  originally projected here, a single "Prepare This Quarter" action was
  going to call `WorksheetEngine.build()` + `run_all_detectors()` +
  `submit_for_approval()` in sequence, all three, automatically. Mike
  modified that directly before any code was written: preparation
  builds the worksheet and runs detectors, but **never** automatically
  submits for approval — `POST /submit` is a separate, deliberate
  action, refusing cleanly if nothing's been prepared or if the
  worksheet was already submitted. This keeps Preparation / Review /
  Approval Routing as three distinct steps, not two. Still
  human-initiated, still no scheduler, still fully inside existing
  boundaries. See `docs/ifta-clerk/PREPARE_THIS_QUARTER_NOTES_v1.md`,
  `PREPARE_THIS_QUARTER_WALKTHROUGH_REPORT_v1.md`.
- **Phase 5.5 — Mileage entry UI (not originally numbered; added
  2026-08-05).** Resolves §12.2, closed above. `POST /record-mileage`
  gives mileage entry a real front door in `dispatch.ifta_clerk`,
  replacing the CLI-only `tools/mileage_worksheet.py` as the normal
  path (the CLI remains, now a thin wrapper around the same shared
  `dispatch.ifta.mileage.record_mileage()`). A non-blocking
  plausibility warning, computed from `live_fleet_mpg_estimate()`
  against the same `DEFAULT_MPG_BAND` `fleet_mpg_out_of_band` already
  uses, surfaces at entry time — never refusing the entry, only
  flagging it earlier than the detector otherwise would. See
  `docs/ifta-clerk/MILEAGE_ENTRY_NOTES_v1.md`.
- **Phase 6 — Recommendation packages, per §11. In progress: one of
  three types built.** Recommended Payment Amount, built and merged
  2026-08-05 — `POST /recommend-payment` wraps a sealed worksheet's own
  `total_net_tax` in a `remit`/`credit`/`no_payment_due` label and
  writes one proposal file to Archive, nothing more. Chosen to build
  first because it has zero external-system dependency, unlike the
  other two, which still require a real DocuSign or accounting-system
  target Mike hasn't specified: a prepared DocuSign package, and a
  drafted accounting notification, both remain future, named only, not
  designed. See `docs/ifta-clerk/PAYMENT_RECOMMENDATION_NOTES_v1.md`,
  `PAYMENT_RECOMMENDATION_WALKTHROUGH_REPORT_v1.md`.

Each phase gets its own launch package, its own tests, its own
walkthrough, and its own explicit sign-off before merge — the same
discipline every prior piece of this system has already used. None of
that starts until this blueprint itself is approved.

---

*End of IFTA_CLERK_BLUEPRINT_v1. Design document only; no code
accompanies it; does not itself open a build session.*

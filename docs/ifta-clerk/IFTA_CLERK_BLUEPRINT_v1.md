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
| Mileage | Mike types it into a form, one entry at a time | Still Mike's input today — this blueprint does not solve mileage (see §3) — but the *form* stops being the point; entry becomes a small, occasional task, not a session |
| Rates | Mike types a new rate row into a form | Unchanged — rate entry is inherently a human-transcribes-a-published-number task; this was never clerical busywork the Clerk should absorb |
| "Is the quarter ready?" | Mike has to think to ask this — nothing tells him | The Clerk knows continuously: how much data exists, what's missing, what's flagged, what's uncertain |
| Build the worksheet | Mike clicks Build | The Clerk prepares the draft itself, at or near quarter-end, without being clicked into it line by line |
| Review | Mike reads a worksheet detail page he had to navigate to | Mike is handed one decision package: numbers, exceptions, missing data, evidence links, confidence — everything needed to say yes or no, nothing he has to go hunting for |
| Approve | Mike clicks Approve in the Queue | Unchanged — this is correctly a human gate already |
| Seal | Mike clicks Seal | The Clerk seals once approval exists — Mike doesn't have to remember to come back and click a third button |
| After sealing | Nothing | Future: a DocuSign package, an accounting notification, and a recommended payment amount, each a **proposal only** — see §11 |

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
- **Vision extraction (`dispatch.receipt.extraction.vision`) — real but
  unexercised.** The code path exists and is wired into the real intake
  pipeline. It has never once run against a live credential anywhere in
  this project: no `ANTHROPIC_API_KEY` has existed in any environment
  this system has run in, so every attempt so far raises
  `VisionExtractionUnavailable` and quarantines. **This is the single
  largest gap between "IFTA Tool" and "IFTA Clerk."** Stage 2 of the
  target workflow (§4) is not a build task — the code is already there —
  it is a credentials-and-verification task, addressed directly in §9.
  See `docs/governance/OCR_VISION_EXTRACTION_DOCTRINE_v1.md` for the
  full architectural doctrine this system already follows for
  extraction — verified, not just asserted, against the real pipeline.
- **Router (Lane C).** Already creates real `FuelRecord`/`ExpenseRecord`
  rows automatically the moment extraction succeeds, CSV or vision alike
  — no new logic needed for "store extracted data automatically."
- **Mileage — the other real, unsolved gap.** Every jurisdiction-mile
  entered into this system, in every walkthrough and every pilot run,
  has been typed in by a human (or a build session standing in for one).
  There is no ELD integration (explicitly out of scope, both in the
  earlier DispatchPilot direction and unchanged here) and no other
  source of truth for miles. The Clerk can automate everything
  *downstream* of having real mileage data. It cannot manufacture
  mileage data that doesn't exist. Named as an open question in §12, not
  resolved here.
- **Exception detectors (Lane C, `exceptions.py`) — ten total, and they
  split cleanly into two groups that matter a great deal for §6 and §8:**
  five (`odometer_discontinuity`, `active_truck_days_no_mileage`,
  `broken_evidence_linkage`, `late_arrival_closed_quarter`,
  `reefer_in_propulsion`) take only a read-only connection and a date
  range — **no worksheet required, real-time, any time.** The other five
  (`fuel_no_miles`, `miles_no_fuel_gap`, `fleet_mpg_out_of_band`,
  `rate_version_mismatch`, `corner_clipping`) take a built worksheet
  dict — they are inherently scoped to a computed aggregate (fleet MPG,
  taxable gallons) that doesn't exist until a worksheet does. This split
  is verified directly against `exceptions.py`'s real function
  signatures, not assumed.
- **Worksheet engine, package builder (Lane C).** `WorksheetEngine.build()`,
  `submit_for_approval()`, `attempt_seal()` are real, tested, and already
  enforce every relevant rule (no fabricated rate, no seal before
  approval, draft-only until sealed). The Clerk calls these same
  functions — it does not need new ones. What changes is *what calls
  them and when* (§10).
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
| 2. OCR / Vision Extraction | Code built; **unexercised against a live credential** (§9) |
| 3. Validation Layer | Built (`validators.py` — structural, sum, confidence, dedup), unchanged |
| 4. Fuel + Expense record creation | Built (Router), unchanged |
| 5. Mileage / jurisdiction accumulation | Fuel side built; **mileage input is an open gap** (§3, §12) |
| 6. IFTA workspace | **Resolved — read-only, §5** |
| 7. Exception queue | Built (ten detectors + real Queue items); **live-preview split analyzed in §8** |
| 8. Review dashboard | **Not built — designed in §7** |
| 9. Mike approval | Built, proven live twice, unchanged |
| 10. IFTA package | Built (`attempt_seal`'s bundle), unchanged |
| 11. Archive | Built, unchanged |
| 12. DocuSign / accounting handoff | **Explicitly future, recommendation packages only** (§11) |

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
   the spec 3.5 arithmetic without writing anything. This does not exist
   today.
3. **The one real, deliberate Build — persists, exactly as it does
   today.** When Mike (or the Phase 3 "Prepare This Quarter" trigger,
   §10) actually decides the quarter is ready, `WorksheetEngine.build()`
   runs for real, once, producing the real draft worksheet, real
   exceptions, and a real audit trail — unchanged from today.

**Recommendation for closing moment 2, not built now, flagged for its
own future approval:** add an optional non-persisting mode to
`WorksheetEngine` itself (e.g. a `preview()` method, or `build(...,
persist=False)`) that runs the identical spec 3.5 arithmetic and returns
the identical shape of result, skipping only the two `INSERT`s. This
keeps the formula in exactly one place — the same tested function, not a
second reimplementation — while giving the dashboard a way to show a
current-estimate number that is, by construction, never mistaken for a
real worksheet, because nothing was ever written. This is a small,
narrowly-scoped change to `worksheet.py`, which is why it is named as a
recommendation here rather than built: it touches a file this session's
own `build/ifta-ui` launch package treated as forbidden-to-edit for good
reason (it's Lane C's frozen core), and a change to it — however small —
deserves the same explicit approval this project has given every prior
change to already-merged lane code (the Evidence Record v1.1 amendment
is the precedent for how that conversation goes).

**What a live estimate is not.** It is not a second source of truth, not
a competing number, and never appears without a label distinguishing it
from a real worksheet's stored, sealed values. Once a real worksheet
exists for the quarter, the dashboard shows *that* — read exactly as
stored, exactly as Reports' own IFTA Position already does — and the
live-estimate path stops being shown at all for that quarter. There is
never a moment where both a live estimate and a real worksheet's numbers
are on screen at once claiming to answer the same question.

## 7. Review Dashboard

One screen, one quarter (and, matching the worksheet engine's own
granularity, one fuel type), assembled entirely from existing sources
per §5's resolution. Seven panels:

1. **Readiness status** — a single rollup label ("ready to prepare" /
   "N exceptions open" / "M records below confidence threshold" /
   "missing mileage for N truck-days"), computed from the panels below,
   still read-only, still no domain judgment — the one genuinely new
   piece of logic on this screen, and a small one.
2. **Miles by jurisdiction** — `mileage_records`, already real.
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
   live estimate (once built); after one exists, Reports' own pattern —
   `total_net_tax` read exactly as stored, never recomputed. Never both
   at once, per §6.

All seven fit inside the read-only, no-recomputation boundary Lane D's
charter already established. None of them requires a new writer.

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

**Category 2 — Live Indicators.** Findings from the five worksheet-free
detectors named in §3 (`odometer_discontinuity`,
`active_truck_days_no_mileage`, `broken_evidence_linkage`,
`late_arrival_closed_quarter`, `reefer_in_propulsion`), called directly
— they are already pure, side-effect-free functions returning finding
lists — **without ever calling `run_all_detectors()`**, so nothing is
persisted and no Queue item is created just because Mike opened a
dashboard. If §6's recommended `WorksheetEngine` preview mode is later
approved and built, the other five detectors (which need a worksheet
dict) can join this live category too, computed against the in-memory
preview worksheet — until then, those five remain visible only after a
real build, in Category 1.

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

**Prerequisite (not this blueprint's to solve).** A real
`ANTHROPIC_API_KEY`, supplied by Mike, configured in whatever real
environment eventually runs this system day to day — not this remote
build environment, which has never held one and has no path to obtaining
one. Nothing below can begin until this exists.

**Stage 1 — Small, supervised extraction trial.** A handful (5-10) of
real or highly realistic receipt images, extracted one at a time, each
field (vendor, date, jurisdiction-bearing address, gallons, fuel type,
total, receipt number) checked by a human against the source image
directly. Purpose: does extraction work at all against real image
input, not synthetic text files standing in for one — every extraction
test in this project so far has used plain-text stand-ins, never an
actual photograph or scan.

**Stage 2 — Confidence calibration.** `DEFAULT_CONFIDENCE_THRESHOLD =
0.75` (`validators.py`) was chosen without ever having a single real
extraction to calibrate against. Once Stage 1 produces real
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

**What this plan is not.** It is not a claim that vision extraction
works — only that the doctrine (§`OCR_VISION_EXTRACTION_DOCTRINE_v1`)
this system already follows for it is sound, verified against real
code, and ready for the day real data can test it.

## 10. What Happens to `build/ifta-ui`

Not defended, not discarded. Its real, tested machinery — `rates.insert_rate()`,
`WorksheetEngine.build()`, `run_all_detectors()`, `submit_for_approval()`,
`attempt_seal()` — is exactly what the Clerk should call. The mistake
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
  approval and sealing today.
- Human approval remains required, explicitly, for: IFTA filing,
  DocuSign/signature package, accounting notification, payment/check
  authorization, and sealing (already true — `attempt_seal()` cannot run
  without a real approval, and that doesn't change).
- No new agents are proposed. The Clerk is a workflow — a scheduling and
  presentation change over existing, real functions — not a new
  autonomous decision-maker.

## 12. Open Questions for Mike

1. **Quarter-end trigger:** should preparing a quarter's draft be a
   single manual "Prepare This Quarter" action (an operator or Mike
   clicks it once, near quarter-end — no new infrastructure, still
   satisfies "the system does the clerical work") or does this blueprint
   need to plan for a real scheduler now? Recommendation: manual trigger
   first — it satisfies the core principle (Mike reviews, doesn't
   perform) without taking on production infrastructure this session
   can't stand up anyway.
2. **Mileage's future.** Is manual entry (already built) acceptable as
   the ongoing source of truth indefinitely, or is there a real future
   plan (an ELD export dropped into DispatchPilot's `ELD` folder, today
   evidence-only with no extraction logic) that should be scoped as a
   later phase? This blueprint doesn't answer it — it flags that the
   Clerk's value is capped by this answer.
3. **Confidence threshold.** What `extraction_confidence` cutoff should
   route a record to "suspect, review before trusting" rather than being
   silently accepted? §9 recommends calibrating this against real data
   before treating 0.75 as more than a placeholder — but a number still
   needs setting, and that's a decision, not a build task.
4. **`build/ifta-ui`'s fate** (§10): merge as a secondary override tool,
   merge but relabel its role in its own docs, or hold it unmerged
   pending the Clerk's first phase?
5. **`WorksheetEngine` preview-mode extension** (§6): approve, in
   principle, a small future change to `worksheet.py` adding a
   non-persisting computation mode — needed to make live estimates and
   Category 2 exception previews possible for the five worksheet-scoped
   detectors, and needed before §7's "estimated tax position" panel can
   show anything before a real worksheet exists. Not built without this
   approval, per the same standard the Evidence Record v1.1 amendment
   already set for touching frozen/already-merged lane code.
6. **Who owns Stage 1-4 of §9** — obtaining and holding the real
   `ANTHROPIC_API_KEY`, and where the validation trial actually runs?
   Outside this repository's or this build session's control either way.

## 13. Phased Build Plan (roadmap, not a launch package)

Each phase is independently shippable and reversible; none commits to
the next.

- **Phase 1 — Surface what already exists.** Expose
  `extraction_confidence` and Category 1 (Confirmed) exceptions in one
  place, read-only. Smallest possible slice, zero new write paths,
  immediately useful regardless of what happens next.
- **Phase 2 — Category 2 Live Indicators.** Wire the five worksheet-free
  detectors (§8) directly into the dashboard, read-only, never queued.
  Still no `WorksheetEngine` change needed — these five already run
  without a worksheet today.
- **Phase 3 — The Review Dashboard, fully assembled** (§7). All seven
  panels, once mileage's role (§12.2) and the confidence threshold
  (§12.3) are answered. "Estimated tax position" shows only Category
  1/real-worksheet numbers until Phase 4.
- **Phase 4 — `WorksheetEngine` preview mode** (§6, §12.5, pending its
  own explicit approval). Unlocks: live tax estimates before a real
  build, and the remaining five detectors joining Category 2.
- **Phase 5 — The Clerk's own trigger.** A single "Prepare This Quarter"
  action that calls `WorksheetEngine.build()` + `run_all_detectors()` +
  `submit_for_approval()` in sequence, itself — replacing three manual
  clicks with the one action a human actually wants to take. Still
  human-initiated, still no scheduler, still fully inside existing
  boundaries.
- **Phase 6 (future, named only, not designed here).** Recommendation
  packages only, per §11: a prepared DocuSign package, a drafted
  accounting notification, a recommended payment amount — proposals,
  never live sends, human-gated at every step.

Each phase gets its own launch package, its own tests, its own
walkthrough, and its own explicit sign-off before merge — the same
discipline every prior piece of this system has already used. None of
that starts until this blueprint itself is approved.

---

*End of IFTA_CLERK_BLUEPRINT_v1. Design document only; no code
accompanies it; does not itself open a build session.*

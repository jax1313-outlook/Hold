# IFTA_CLERK_BLUEPRINT_v1

Design correction and future build plan. **No code changes accompany
this document.** Written in response to a direct correction of the
`build/ifta-ui` direction (2026-08-04): that package is a real, working
*tool*, but a tool is not what was asked for. This document defines what
was actually asked for — an IFTA *Clerk* — and how Dispatch gets there
without discarding what already exists or overbuilding what doesn't need
to exist yet.

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
| After sealing | Nothing | Future: DocuSign package prepared, accounting notified, a recommended payment amount surfaced — all proposals, all human-gated (§8) |

## 3. What Already Exists That the Clerk Can Be Built On

Stated honestly — some of this is fully proven, some is real but
unexercised, and one piece is a genuine, unsolved gap.

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
  (a scheduler) and is explicitly out of this blueprint's scope* (§8) —
  named here as a real prerequisite, not solved by this document.
- **Vision extraction (`dispatch.receipt.extraction.vision`) — real but
  unexercised.** The code path exists and is wired into the real intake
  pipeline. It has never once run against a live credential anywhere in
  this project: no `ANTHROPIC_API_KEY` has existed in any environment
  this system has run in, so every attempt so far raises
  `VisionExtractionUnavailable` and quarantines. **This is the single
  largest gap between "IFTA Tool" and "IFTA Clerk."** Step 2 of the
  target workflow (OCR reads a scanned receipt) is not a build task —
  the code is already there — it is a credentials-and-verification task.
  Nothing in this blueprint can close that gap; it can only name it
  plainly rather than imply the Clerk already reads photographs today.
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
  mileage data that doesn't exist. This is named as an open question in
  §9, not resolved here.
- **Exception detectors (Lane C, `exceptions.py`).** Already fully
  built — all ten, already covering most of "missing data" and "suspect
  entries" by name: `fuel_no_miles`, `miles_no_fuel_gap`,
  `active_truck_days_no_mileage`, and `fleet_mpg_out_of_band` already
  detect exactly the shapes of missing/suspect data the target workflow
  asks for. No new detector logic is required for the review dashboard's
  "exceptions" and "missing data" panels — they already exist; they just
  aren't surfaced anywhere Mike would see them at a glance yet.
- **Worksheet engine, package builder (Lane C).** `WorksheetEngine.build()`,
  `submit_for_approval()`, `attempt_seal()` are real, tested, and already
  enforce every relevant rule (no fabricated rate, no seal before
  approval, draft-only until sealed). The Clerk calls these same
  functions — it does not need new ones. What changes is *what calls
  them and when* (§7).
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

| Stage | Status |
|---|---|
| 1. OCR / Intake | Intake surface built (DispatchPilot); vision extraction code built but unexercised (no live credential) |
| 2. Evidence Spine | Built, proven, unchanged |
| 3. Fuel + Expense extraction | Built (Router), unchanged |
| 4. Mileage / jurisdiction accumulation | Fuel side built; **mileage input is an open gap** (§3, §9) |
| 5. IFTA workspace | **Not built — needs definition** (§5) |
| 6. Exception queue | Built (ten detectors + real Queue items), unchanged |
| 7. Review dashboard | **Not built — needs new work**, but built substantially from existing reads (§6) |
| 8. Mike approval | Built, proven live twice, unchanged |
| 9. IFTA package | Built (`attempt_seal`'s bundle), unchanged |
| 10. Archive | Built, unchanged |
| 11. DocuSign / accounting handoff | **Explicitly future, explicitly out of scope now** (§8) |

Six of eleven stages (2, 3, 6, 8, 9, 10) need no new work at all — built,
proven, unchanged by this blueprint. One (1, intake/OCR) is built but
unverified against a live credential. One (4, mileage) is a real, named
gap this blueprint does not close. Two (5, 7 — workspace, dashboard) are
where the actual new work is. One (11) is future and explicitly out of
scope now.

## 5. The "IFTA Workspace" — What It Should and Shouldn't Be

This is the one genuinely new concept in the target workflow, and it
carries a real design fork worth naming explicitly rather than deciding
silently.

**Option A (recommended): a read-only aggregation, not a new data
store.** `fuel_records`, `expense_records`, and `mileage_records` already
*are* the accumulation — every fuel purchase and every mileage entry is
already sitting in governed tables from the moment it's recorded, all
quarter long. "Holding data in a workspace until review time" doesn't
require a new place to hold it; it requires a new *view* over where it
already is: "for quarter 2026-Q3, here's everything accumulated so far."
This is a Reports-shaped problem — arithmetic and grouping over existing
records, no domain judgment, no recomputation of anything Lane C already
computes — and it fits inside `REPORTS_CHARTER_v1.md`'s existing bright
lines without needing a new contract at all.

**Option B: a new mutable "draft" status Mike's data passes through.**
Records would carry a workspace-membership or readiness flag before
being "confirmed" into worksheet-eligibility. This is heavier — it's a
new field on frozen contracts, a new state machine, and a real question
about who/what transitions a record through it — and nothing in the
target workflow actually requires it: a fuel purchase is either real
evidence with a real `FuelRecord` or it isn't; there's no meaningful
intermediate "not yet in the workspace" state for data that's already
correctly extracted and routed.

**Recommendation: Option A.** The "workspace" is the Review Dashboard
(§6) itself — a live, always-current read over this quarter's real data
— not a new place data sits before becoming real. This is flagged as a
decision for Mike, not assumed silently, in §9.

## 6. The Review / Decision Dashboard

Concretely, "readiness" resolves to seven real things, five of which
already exist as data and need only be surfaced together in one place:

- **Miles by jurisdiction** — `mileage_records`, already real.
- **Fuel by jurisdiction** — `fuel_records`, already real (this is
  what Fuel Spend already shows, filtered to the quarter).
- **Exceptions** — `ifta_exceptions`, already real, already detected by
  all ten existing detectors.
- **Missing data** — mostly already covered by name (`fuel_no_miles`,
  `active_truck_days_no_mileage`); the dashboard's job is to make these
  visible at a glance rather than requiring Mike to open the Queue and
  read subject lines.
- **Suspect entries** — genuinely new, small surface area:
  `extraction_confidence` already exists as a field on every
  `FuelRecord`/`ExpenseRecord` but is not currently surfaced anywhere in
  Reports or the Queue. Exposing "N records below a confidence
  threshold" is a small, real addition, still read-only.
- **Estimated tax due** — already computed and stored
  (`ifta_worksheets.total_net_tax`), already read-only per Reports'
  existing IFTA Position pattern — read exactly as stored, never
  recomputed here either.
- **Evidence links** — `EvidenceSpine.retrieve()` with hash
  re-verification, the exact pattern Lane B's own Queue detail page
  already uses for evidence previews. Reusable directly.
- **Confidence / readiness status** — the one new piece of judgment-free
  logic: a rollup like "ready" / "N exceptions open" / "M records below
  confidence threshold" / "missing mileage for N truck-days" — computed
  from the above, still read-only, still no domain judgment, same as
  every other Reports-shaped read in this system.

All seven fit inside the read-only, no-recomputation boundary Lane D's
charter already established. None of them requires a new writer.

## 7. What Happens to `build/ifta-ui`

Not defended, not discarded. Its real, tested machinery — `rates.insert_rate()`,
`WorksheetEngine.build()`, `run_all_detectors()`, `submit_for_approval()`,
`attempt_seal()` — is exactly what the Clerk should call. The mistake
wasn't the underlying calls; it was making *button-clicking through
them* the primary interface. Recommendation: the manual UI remains
useful as a secondary, explicit **override and inspection tool** —
backfilling a missed quarter, correcting something the Clerk flagged,
looking at a worksheet's raw detail — but stops being the thing Mike
uses every quarter. Whether it merges as-is, merges with its role
relabeled, or waits until the Clerk exists is a decision for Mike (§9),
not decided unilaterally here.

## 8. Boundaries (restated as commitments)

- Matrix Group 1's architecture is unchanged. Evidence Spine, Queue, and
  the Receipt→IFTA chain are used as they already exist, not forked or
  duplicated.
- No alternate evidence path, no bypass of Evidence Spine, no bypass of
  Manager Queue approval.
- No live QuickBooks writes, no live DocuSign integration, no real tax
  authority filing, no production infrastructure, no autonomous filing
  or payment — none of this is built now.
- Human approval remains required, explicitly, for: IFTA filing,
  DocuSign/signature package, accounting notification, payment/check
  authorization, and sealing (already true — `attempt_seal()` cannot run
  without a real approval, and that doesn't change).
- No new agents are proposed. The Clerk is a workflow — a scheduling and
  presentation change over existing, real functions — not a new
  autonomous decision-maker.

## 9. Open Questions for Mike

1. **Workspace shape:** confirm Option A (§5, read-only dashboard over
   existing tables) over Option B (a new mutable draft state) — or say
   why B is actually wanted.
2. **Quarter-end trigger:** should preparing a quarter's draft be a
   single manual "Prepare This Quarter" action (an operator or Mike
   clicks it once, near quarter-end — no new infrastructure, still
   satisfies "the system does the clerical work") or does this blueprint
   need to plan for a real scheduler now? Recommendation: manual trigger
   first — it satisfies the core principle (Mike reviews, doesn't
   perform) without taking on production infrastructure this session
   can't stand up anyway.
3. **Mileage's future.** Is manual entry (already built) acceptable as
   the ongoing source of truth indefinitely, or is there a real future
   plan (an ELD export dropped into DispatchPilot's `ELD` folder, today
   evidence-only with no extraction logic) that should be scoped as a
   later phase? This blueprint doesn't answer it — it flags that the
   Clerk's value is capped by this answer.
4. **Confidence threshold.** What `extraction_confidence` cutoff should
   route a record to "suspect, review before trusting" rather than being
   silently accepted? A number, not a judgment call this document should
   make.
5. **`build/ifta-ui`'s fate** (§7): merge as a secondary override tool,
   merge but relabel its role in its own docs, or hold it unmerged
   pending the Clerk's first phase?

## 10. Phased Build Plan (roadmap, not a launch package)

Each phase is independently shippable and reversible; none commits to
the next.

- **Phase 1 — Surface what already exists.** Expose `extraction_confidence`
  and the existing exception detectors' findings in one place, read-only.
  Smallest possible slice, zero new write paths, immediately useful on
  its own regardless of what happens next.
- **Phase 2 — The Review Dashboard** (§6, Option A from §5). One screen,
  one quarter, everything Mike needs to decide — built once mileage's
  role (§9.3) and the confidence threshold (§9.4) are answered.
- **Phase 3 — The Clerk's own trigger.** A single "Prepare This Quarter"
  action that calls `WorksheetEngine.build()` + `run_all_detectors()` +
  `submit_for_approval()` in sequence, itself — replacing three manual
  clicks with the one action a human actually wants to take ("get this
  quarter ready for me to look at"). Still human-initiated, still no
  scheduler, still fully inside existing boundaries.
- **Phase 4 (future, named only, not designed here).** DocuSign package
  preparation, accounting/QuickBooks notification, recommended payment
  amount — proposals only, human-gated at every step, exactly as §8
  requires.

Each phase gets its own launch package, its own tests, its own
walkthrough, and its own explicit sign-off before merge — the same
discipline every prior piece of this system has already used. None of
that starts until this blueprint itself is approved.

---

*End of IFTA_CLERK_BLUEPRINT_v1. Design document only; no code
accompanies it; does not itself open a build session.*

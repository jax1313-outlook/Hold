# DISPATCH PILOT — RUN 2 REPORT (through the Shell)

Purpose: repeat the operational pilot exercise, this time driving as
much of the workflow as possible **through `dispatch.shell`** — the
unified presentation layer just built and merged — rather than raw
Python calls, to learn whether it actually improves the operational
experience it was built for. Run against `integration` @ `d53caba`, in
this environment.

## Sandbox

`/home/user/dispatch_pilot_run2/` — kept intact, same as Run 1, for the
same reason: this run is itself the deliverable.

## The scenario

A different, slightly larger week than Run 1 — three jurisdictions (TX,
TX, OK) instead of two, six files instead of nine, dropped as one batch:
three clean fuel purchases, one combined meals+truck-wash receipt file,
a rate confirmation, and a proof of delivery. Mileage (TX 2,050mi, OK
690mi) and the IFTA worksheet were built the same way as Run 1 (no web
UI exists for this yet — see Findings).

## What went through the Shell this time, that Run 1 did not

- **Process Inbox**: clicked through the real `/pilot` button (Run 1
  called `process_inbox()` directly in Python). All 6 files routed
  correctly — 4 to Fuel/Receipts via the real Lane C pipeline, 2 held
  for review (POD, RateCon) via the real Evidence Spine.
- **IFTA approval**: found the real approval queue item by following a
  link from the dashboard to `/queue/`, opened its detail page, and
  clicked **Approve** with a real decision note — through the Shell's
  mounted Queue, not `QueueStore.approve()` called directly. This is
  genuinely new ground: Run 1 and the Shell's own walkthrough both used
  Python/`resolve()` for their queue actions; this is the first time an
  IFTA approval specifically went through the mounted UI.
- **All three report types + Save For Printing**: run through
  `/reports/`, not `dispatch.reports.queries` directly.
- **The dashboard** was checked before and after each phase, and
  correctly reflected: 6 items in Inbox → 0 after processing; 0 open
  queue items → 4 (2 held-for-review, 1 IFTA exception, 1 IFTA approval)
  → 3 after the approval was actioned; the saved report appearing under
  Recent reports.

## Results, independently verified

Every number the Shell displayed matched the raw database exactly:
Fuel Spend $1,224.70 / 287.0gal (TX $856.50/199gal, OK $368.20/88gal);
Expense Summary $1,283.45 across `fuel`/`meals`/`truck_wash`; IFTA
Position $0.31 net tax, 1 exception, `sealed` status — all confirmed
against `fuel_records`, `ifta_worksheets`, and `queue_items` directly.
22 real audit entries, zero server errors across the entire run.

## Findings

1. **The unification genuinely works, not just in theory.** Every step
   except mileage entry, worksheet build, and seal happened in one
   browser session at one port — drop files, click Process Inbox, follow
   a dashboard link to the flagged approval item, approve it, follow
   another link to Reports, run and save. No separate terminals, no port
   juggling. This is the concrete improvement the Shell was built to
   deliver, and this run is the first time it's been exercised this way
   rather than asserted.
2. **A real, honest gap: IFTA still has no web UI for the parts that
   matter most.** Mileage entry, worksheet building, and sealing are
   still Python/CLI-only — only the *approval* step (a Queue item) has a
   UI, because Lane B's Queue already had one. Mike could review and
   approve an IFTA worksheet through the Shell today, but someone still
   has to run `tools/mileage_worksheet.py` and construct a
   `WorksheetEngine` by hand to get that worksheet built in the first
   place. This is exactly the kind of thing "Fix Real Problems As They
   Appear" is for — not fixed here, flagged here.
3. **The fleet-MPG detector fired again, on different synthetic
   numbers.** 9.55 vs. the plausible band's 9.5 ceiling — the second
   pilot run in a row where entered mileage produced a borderline/
   implausible fleet MPG. Reinforces Run 1's finding: manual mileage
   entry is this system's one input with no independent cross-check, and
   it's now shown up twice.

No crashes, no silent failures, no fabricated data, nothing hidden — the
same standard as every walkthrough and pilot run before this one.

## What this report is not

Same as every report before it: evidence, not a decision or a
certification. The sandbox is left intact for direct inspection.

---

*End of DISPATCH PILOT — RUN 2 REPORT.*

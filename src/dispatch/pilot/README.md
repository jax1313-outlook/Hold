# dispatch.pilot — DispatchPilot's Inbox sorter

The simple pilot input workflow: Mike drops files into
`DispatchPilot\Inbox`; `process_inbox(config)` sorts them into
`Fuel`, `Receipts`, `RateCons`, `POD`, `ELD`, or `Misc`, once per call —
no watcher, no daemon, no Outlook/email/ELD integration. A cron job, a
manual trigger, or a scheduled task outside this codebase is what turns
this into a "watcher" operationally, the same pattern
`dispatch.receipt.intake.process_drop` already established.

`DispatchPilot` itself lives under the existing, FROZEN `operations` root
(`<OPERATIONS>\DispatchPilot\...`) — no config or contract change was
needed for the folder tree itself, only for what document types the
Evidence Spine would accept (see below).

## Two paths, one governed evidence system

Every file goes through exactly one of two paths — never a third,
lower-trust one:

1. **A real receipt** (fuel/expense-shaped: `.csv`, or an image/PDF
   Dispatch can attempt vision extraction on) is staged into the real
   `Operations\Intake\Drop` and run through Lane C's actual, unmodified
   `IntakePipeline` — the exact code every prior walkthrough already
   proved. A copy of the source lands in `Fuel` (produced a FuelRecord)
   or `Receipts` (expense-only); a file that fails outright stays exactly
   where Lane C's own pipeline already puts it (`Intake\Quarantine`),
   surfaced through the real Queue.
2. **A document type this system doesn't have processing logic for yet**
   (RateCon, POD, ELD) or genuinely unrecognized (`Misc`) is registered
   as real governed evidence via the real, unmodified
   `EvidenceSpine.register()` — the **Evidence First Doctrine**
   (`docs/decisions/DECISION_LOG.md`, 2026-08-04): a legitimate business
   artifact is evidence whether or not this system can process its
   contents yet. Filed into the matching folder, with a non-urgent
   (`whenever`) `review` queue item — distinguishable on sight from a
   genuine intake failure, which is `urgent`/`exception`.

Mike explicitly rejected a secondary or reduced-trust evidence path when
approving the contract amendment that made path 2 possible
(`evidence_record.schema.json` v1.0 → v1.1): every document type gets the
same real, hash-verified, audited treatment.

## Classification is deterministic, never inferred

A filename-token match (`ratecon`/`ratecons`/`rc` → RateCons, `pod` →
POD, `eld` → ELD — bounded to whole tokens, so `tripod.pdf` doesn't
false-match `pod`) wins over everything else: the human's own label on
the file is the strongest signal this system has, matching the existing
"data, not inference" precedent Lane C's vendor-profile matcher already
set. With no keyword match, a bounded set of extensions Dispatch can
actually attempt extraction on (`.csv`, `.pdf`, `.jpg`, `.jpeg`, `.png`)
goes through the real receipt pipeline; anything else lands in `Misc` as
`unclassified` — the honest label for "doesn't match any known type,"
never a guess at one of the others.

## Known simplifications (smallest practical pilot, not perfect automation)

- A single file with **both** fuel and non-fuel lines (a mixed CSV
  export) is filed wherever its most notable outcome is — `Fuel`, if any
  line produced a FuelRecord — not split across two folders.
- A file that registers and extracts but has **every** line quarantined
  (e.g. every line fails validation) isn't copied into any
  `DispatchPilot` folder; it's visible through the Queue and Lane C's own
  `Intake\Processing`, the same as it already would be without the pilot
  wrapper.
- No real extraction logic exists for RateCon/POD/ELD *content* yet —
  this pilot proves the intake/evidence/queue mechanics around them, not
  what's inside them. That's deliberately left for what the pilot
  teaches, not guessed at now.

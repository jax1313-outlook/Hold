# DispatchPilot — Input Workflow — NOTES

Per the direction to complete Matrix Group 1, then move fast into an
operational pilot to maximize learning through actual use (bugs expected
and acceptable; the goal is operational learning, not certification).

## Built

- `src/dispatch/pilot/intake.py` — `PilotIntake` / `process_inbox(config)`.
  Sorts `DispatchPilot\Inbox` into `Fuel`, `Receipts`, `RateCons`, `POD`,
  `ELD`, `Misc`, once per call, no daemon/watcher.
  - Receipt-shaped files (`.csv`, or an image/PDF Dispatch can attempt
    vision extraction on) go through Lane C's real, unmodified
    `IntakePipeline` — same code every prior walkthrough proved.
  - RateCon/POD/ELD/unrecognized files register as real governed evidence
    via the real, unmodified `EvidenceSpine.register()` (Evidence First
    Doctrine, evidence_record v1.1 — see `docs/decisions/DECISION_LOG.md`)
    and get a non-urgent (`whenever`) `review` queue item, distinguishable
    from a genuine intake failure (`urgent`/`exception`).
  - Classification is a deterministic, token-bounded filename-keyword
    match, then a bounded extension allowlist — never an inference about
    document contents.
- `tools/init_pilot.py` — creates the `DispatchPilot` folder skeleton
  under the existing OPERATIONS root. No config/contract change was
  needed for the folder tree itself.
- `tests/pilot/` — 30 tests: classification correctness (including a
  token-boundary false-positive guard, `tripod.pdf` must not match
  `pod`), real end-to-end routing for every document type, the real
  quarantine/failure path, queue-item priority/type correctness, full
  audit-trail coverage, and batch/idempotency behavior. Full repo suite:
  343 passed.
- Manual smoke test (real, unedited terminal output, same standard every
  lane's walkthrough used): a 7-file realistic batch (clean fuel CSV,
  clean meal CSV, a malformed CSV, a RateCon, a POD, an ELD export, and a
  genuinely unclear file) dropped into a real Inbox and processed for
  real. All seven classified correctly on the first run, including
  `eld_export_week.csv` correctly caught by the `eld` keyword ahead of
  the `.csv` fallback. Independently verified outside the code that
  produced it: filesystem contents per folder, real SHA-256 hashes in
  `evidence_records`, byte-identical file copies, and a complete 20-entry
  audit trail with no errors.

## Flagged (design decisions made, not litigated further here)

- A single file with both fuel and non-fuel lines (mixed CSV) files under
  `Fuel` only — not split across folders. Documented in the module
  README as a deliberate simplification.
- A file that registers and extracts but has every line quarantined
  (valid shape, bad data) isn't copied into any `DispatchPilot` folder —
  it's visible via the Queue and Lane C's own `Intake\Processing`, same
  as it already would be without this wrapper. Confirmed directly in the
  manual smoke test (`broken_export.csv`'s one bad line quarantined via
  `sum_mismatch`; the file itself was never touched beyond that).
- `DispatchPilot` lives under the existing FROZEN `operations` root
  (`<OPERATIONS>\DispatchPilot\...`), not a new top-level root — the
  config contract's `roots` object is closed (`additionalProperties:
  false`), and a fourth root wasn't needed for a folder that's really
  part of the living OPERATIONS tier, the same way `Intake\Drop` already
  is.

## Deliberately Not Built

- No real extraction/parsing logic for what's *inside* a RateCon, POD, or
  ELD file — this pilot proves the intake/evidence/queue mechanics around
  them, not their content. That's exactly what running the pilot is
  meant to teach, not something to guess at now.
- No Outlook integration, no email ingestion, no ELD system integration —
  explicitly out of scope per direction. Manual drop only.
- No scheduler/watcher — `process_inbox()` is a function called once per
  invocation, same as `process_drop()`. Turning it into a recurring job
  is an operational choice for whoever runs the pilot, not something this
  module owns.

# DISPATCH_IFTA_UI_LAUNCH_PACKAGE_v1

Documentation only; no implementation code. Written per the brainstorming
process (2026-08-04), following the same launch-package convention every
prior lane and the Shell/Pilot phases used. Validated with Mike across
four clarifying rounds before being written: mounting architecture, rate
entry, build/submit as separate steps, and quarter selection are all
resolved below — see `docs/decisions/DECISION_LOG.md` for the record of
each. One additional design judgment call (folding exception detection
into the Build action) was proposed and explicitly confirmed in the same
round.

## 1. Mission

Two real pilot runs through `dispatch.shell`
(`docs/pilot/DISPATCH_PILOT_RUN_2_REPORT_v1.md`, finding #2) surfaced the
same gap twice: mileage entry, worksheet building, and sealing all
require Python/CLI today — only the approval *decision* is reachable
through the web, via the mounted Queue. This package closes that gap
with `dispatch.ifta.app`, a new Flask app mounted at `/ifta` under the
shell, the same `DispatcherMiddleware` pattern already proven for Queue
and Reports.

This is explicitly **not** a new computation engine, a new exception
detector, or a reinterpretation of any IFTA doctrine. Every write action
this UI offers calls an existing, already-tested function in
`src/dispatch/ifta/**` — `WorksheetEngine.build()`, `run_all_detectors()`,
`rates.insert_rate()`, `package.submit_for_approval()`,
`package.attempt_seal()` — none modified, none reimplemented. The UI is
a thin wrapper, the same shape Queue's own UI already is over
`QueueStore`.

## 2. Files to create

- `src/dispatch/ifta/app.py` — `create_app(config)`:
  - `GET /` — lists existing worksheets (quarter, fuel_type, status);
    the Build Worksheet form, pre-filled with the current quarter
    (`quarter_label_for_date(date.today())`, the same derivation Reports'
    IFTA Position already uses — duplicated here, not imported, matching
    the precedent every read-only duplication in this codebase already
    set) and `fuel_type=diesel`; a rate-table-version picker populated
    from `rates.distinct_versions_for()` against the selected quarter/fuel
    type — never a version invented or guessed.
  - `POST /build` — calls `WorksheetEngine.build()` then, on success,
    `run_all_detectors()` against the same worksheet, in one request.
    `MissingRateError`/`InsufficientDataError` render a clear message on
    the form, never a raw 500 — the same "never fabricate, never crash
    silently" instinct Reports and the Shell's Pilot page already apply
    to their own write actions.
  - `GET /worksheets/<id>` — the worksheet: fleet_mpg, total_net_tax,
    per-jurisdiction lines, every exception finding from the Build step,
    status, and:
    - **Submit for Approval** button (visible only if `status == "draft"`
      and no `queue_item_id` yet) — calls `package.submit_for_approval()`.
    - **Seal** button — always visible once submitted, but disabled with
      a clear reason ("waiting on approval — see Queue") unless the
      linked queue item's status is actually `approved`. Clicking it
      calls `package.attempt_seal()`, whose existing refusal
      (`ApprovalNotYetGrantedError`) is preserved exactly — the UI does
      not add, loosen, or duplicate that check, only surfaces it.
  - `GET /rates`, `POST /rates` — lists existing `rate_tables` rows
    (grouped by jurisdiction/quarter/fuel_type); a plain entry form
    (jurisdiction, quarter, fuel_type, rate, surcharge, source_version)
    that calls `rates.insert_rate()` — mechanical transcription only, per
    `IFTA_CONSTITUTION_v1`'s boundary clause ("applies published rate
    tables mechanically... never adjusts source data"). `rate_tables`
    stays INSERT-only exactly as it is today; this form cannot edit or
    remove a row, only add one under a new `source_version`.
  - `GET /mileage`, `POST /mileage` — replaces `tools/mileage_worksheet.py`
    as the primary way mileage gets entered; calls `record_mileage()`
    unmodified (unit_number, jurisdiction, period_start, period_end,
    miles, `entered_by` — required, no default, matching the CLI tool's
    own "no fabrication" field).
- `src/dispatch/ifta/templates/{base,index,worksheet,rates,mileage}.html`
- `src/dispatch/ifta/static/style.css` — own copy of the same minimal
  look every other screen in this system already uses (not shared
  cross-app, same reasoning as the Shell's own stylesheet).
- `src/dispatch/ifta/README.md`
- One line added to `src/dispatch/shell/app.py`'s `create_app()`:
  mounting `dispatch.ifta.app.create_app(config)` at `/ifta`, the exact
  same pattern already used for `/queue` and `/reports` — no other
  change to that file.
- `tests/ifta_ui/__init__.py`, `tests/ifta_ui/conftest.py`,
  `tests/ifta_ui/test_app.py`

## 3. Files to modify

- `src/dispatch/shell/app.py` — **one line**, adding the `/ifta` mount.
  Everything else in that file is untouched; verified the same way
  Queue's and Reports' "zero diffs" were verified for the Shell package
  (`git diff --stat`), scoped here to "no diff except the one mount
  line."
- `docs/pilot/DISPATCH_PILOT_RUN_2_REPORT_v1.md`'s finding #2 is not
  edited (pilot reports are a historical record, not living docs), but
  is superseded by this package's existence — noted in
  `docs/ifta-ui/NOTES.md` at build time, not by rewriting history.

**Forbidden:** editing anything under `src/dispatch/ifta/{rates,worksheet,exceptions,package}.py`
(import and call their existing public functions freely — never modify
their files, their computation logic, or their exception list);
`src/dispatch/{queue,reports,pilot}/**` (this package doesn't need
anything from them); any recomputation of a value `WorksheetEngine`
already computed; any UI path that submits a worksheet as `sealed`
without going through the real approval check; any change to
`IFTA_CONSTITUTION_v1.md`'s boundary clause or exception list.

## 4. Dependencies

- Real functions this package calls but never reimplements:
  `dispatch.ifta.worksheet.WorksheetEngine` (`build`, `get`,
  `quarter_bounds`), `dispatch.ifta.exceptions.run_all_detectors`,
  `dispatch.ifta.rates.{insert_rate,get_rate,distinct_versions_for}`,
  `dispatch.ifta.package.{submit_for_approval,attempt_seal}`,
  `dispatch.ifta.readonly.open_read_only` (the same source-immutability
  enforcement `WorksheetEngine` itself already requires — this app opens
  its own, per the same "duplicate the read-only connection, don't
  import it across a boundary" precedent Reports and the Shell both
  already follow), `dispatch.common.db.bootstrap`,
  `dispatch.evidence.interface.EvidenceSpine` (required by
  `run_all_detectors`'s `broken_evidence_linkage` check),
  `dispatch.queue.store.QueueStore` (required by
  `submit_for_approval`/`attempt_seal`, and to check a worksheet's linked
  queue item's status for the Seal button's enabled/disabled state).
- No new third-party dependency — Flask is already a requirement.

## 5. Contract references

None new. This package touches no FROZEN contract and defines no new
schema — every table it writes to (`rate_tables`, `ifta_worksheets`,
`ifta_worksheet_lines`, `ifta_exceptions`, `mileage_records`,
`queue_items`) already exists, already governed by Lane C's and Lane A's
own schema/triggers.

## 6. Test requirements

- **Build produces a worksheet and its exceptions together, for real.**
  Seed real fuel/mileage records (through the real pipelines, not
  hand-typed rows — same standard `tests/lane_d/`, `tests/pilot/` already
  set); `POST /build`; confirm the response shows both the worksheet
  numbers and any real exception findings, and that both are actually
  persisted (`ifta_worksheets`, `ifta_worksheet_lines`, `ifta_exceptions`
  rows, plus real Queue items for each finding).
- **Missing rate / insufficient data render clearly, not a 500.** A
  `MissingRateError`/`InsufficientDataError` from a real, deliberately
  incomplete scenario shows a clear message on the Build form.
- **Seal is genuinely blocked before approval, and genuinely works
  after.** The real `ApprovalNotYetGrantedError` path, then a real
  `queue.approve()` (through the mounted Queue, matching how Pilot Run 2
  already proved this specific flow works), then a real seal, with the
  sealed bundle independently confirmed on disk — same proof technique
  every prior IFTA walkthrough already used.
- **Rate entry is append-only.** A negative test: no route in this
  package issues `UPDATE rate_tables` or `DELETE FROM rate_tables`
  anywhere (grep guard, same technique as the Shell's no-raw-SQL-write
  test).
- **Mileage entry matches the CLI tool's own behavior exactly** — same
  required fields, same `source=manual_worksheet` default, run side by
  side against `tools/mileage_worksheet.py`'s existing tests' fixtures to
  confirm no divergence.
- **Mounted correctly.** `/ifta` reachable through the shell, its static
  assets resolve under the mount prefix, and — the same class of check
  that already caught nothing wrong in the Shell's own walkthrough but is
  worth repeating on principle — a link generated by this app's own
  templates resolves correctly under `/ifta/...`.
- **Zero diff outside the one mount line.** `git diff --stat` on
  `src/dispatch/shell/app.py` shows only the new mount, nothing else.

## 7. Acceptance criteria (Definition of Done)

- Mike can, entirely through the browser: enter mileage, enter a rate,
  build a worksheet and see its exceptions, submit for approval, approve
  it through the existing mounted Queue, and seal it — with the sealed
  bundle landing on disk exactly as it does today.
- Every write action maps to an existing, unmodified function in
  `src/dispatch/ifta/**` — no new business logic, no recomputation, no
  loosened check.
- All test requirements in §6 green, including a live manual smoke test
  against the real mounted server.
- `src/dispatch/ifta/README.md` written.
- `docs/ifta-ui/NOTES.md` written (Built / Flagged / Deliberately Not
  Built, same convention as every prior phase), explicitly noting this
  closes the gap `docs/pilot/DISPATCH_PILOT_RUN_2_REPORT_v1.md` found.
- Full repo test suite green.
- Branch ready for `integration`; Mike's walkthrough (same standing
  procedure) and explicit sign-off still required before merge.

## 8. Expected deliverables

Working `dispatch.ifta.app` (mileage entry, rate entry, build +
exceptions, submit, seal — all real, all mounted at `/ifta`); one mount
line added to `src/dispatch/shell/app.py`; `tests/ifta_ui/` green;
`src/dispatch/ifta/README.md`; `docs/ifta-ui/NOTES.md`; branch ready for
`integration`.

## 9. Risks

1. **A worksheet built with genuinely wrong mileage still looks
   authoritative on screen.** Both pilot runs entered mileage that
   triggered `fleet_mpg_out_of_band` — this UI doesn't change that
   underlying risk (mileage remains the one input in this whole system
   with no independent cross-check), it just makes it easier to trigger
   more often, since building a worksheet is now one click instead of a
   Python session. Mitigation: exceptions render prominently alongside
   the worksheet, not buried — the same "never hide a flag" instinct
   every prior screen in this system already applies. Not solved here;
   flagged, per `docs/pilot/DISPATCH_PILOT_RUN_2_REPORT_v1.md`'s own
   framing, as a candidate for a future round if it keeps happening with
   real (not synthetic) mileage.
2. **Rate entry is a real, unrecoverable-by-UI mistake if mistyped.**
   `rate_tables` is INSERT-only by design (a correction is a new row, not
   an edit) — this is correct and deliberate, but means a typo in the UI
   creates a permanent row, same as it would via direct SQL today. Not a
   regression; explicitly the existing, accepted trade-off, restated
   here so it isn't rediscovered as a surprise later.
3. **The Seal button's disabled state depends on reading Queue state
   correctly.** If the linked queue item's status check has a bug, Seal
   could either wrongly stay disabled (annoying) or wrongly appear
   enabled (caught anyway by the real, unmodified `attempt_seal()`
   refusal underneath — worst case is a confusing UI, never a bad seal).
   Mitigated by testing the disabled/enabled state directly, not just
   the underlying refusal.

## 10. Rollback plan

Trivial — `dispatch.ifta.app` is new and additive; the one line it adds
to the shell is a single mount entry. Reverting that one line (or simply
not deploying this package) returns the system to exactly its current
state: mileage/rate/build/seal via CLI, approval via the already-working
mounted Queue.

---

*End of DISPATCH_IFTA_UI_LAUNCH_PACKAGE_v1. Documentation only; no
implementation code; does not itself open a build session.*

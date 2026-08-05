# dispatch.ifta_clerk — the Review Dashboard

The primary user experience of the IFTA Clerk
(`docs/ifta-clerk/IFTA_CLERK_BLUEPRINT_v1.md` section 7, approved
2026-08-04). One screen, one quarter, one fuel type, assembled entirely
from real, already-governed sources — no new table, no duplicate store.
Gained its first two write actions, Prepare This Quarter and Submit for
Approval, on 2026-08-04 (see below) — `dashboard.py` itself remains
exactly as read-only as it was before them.

```python
from dispatch.ifta_clerk.app import create_app

app = create_app(config)
app.run()
```

Mounted at `/ifta-clerk` under the Shell, alongside `/queue`, `/reports`,
and `/ifta`.

## The seven panels (`dashboard.py`)

`build_dashboard(read_only_conn, *, quarter, fuel_type)` assembles all
seven from a single read-only connection — the same structural guarantee
`dispatch.ifta.worksheet.preview()` and
`dispatch.ifta.live_indicators.live_indicators()` already use. No writer
anywhere in this package.

1. **Readiness status** — one rollup label, computed from the panels
   below. The one genuinely new piece of logic here; still pure
   computation over already-fetched data.
2. **Miles by jurisdiction** — direct read from `mileage_records`.
3. **Fuel by jurisdiction** — direct read from `fuel_records`.
4. **Exceptions and missing data** — Category 1 (`ifta_exceptions`, real,
   queued, from a real build) and Category 2
   (`dispatch.ifta.live_indicators`, live, never persisted) rendered
   distinctly, never merged into one list.
5. **Suspect entries** — `fuel_records`/`expense_records` below
   `DEFAULT_CONFIDENCE_THRESHOLD` (0.75, the same unvalidated placeholder
   `validators.py` uses — labeled as such, see
   `IFTA_CLERK_BLUEPRINT_v1.md` sections 9/12.3).
6. **Evidence links** — plain references (`document_type`,
   `archive_path`, `file_hash`) via a direct join against
   `evidence_records`. Deliberately **does not** call
   `EvidenceSpine.retrieve()` — see "Why panel 6 doesn't call retrieve()"
   below.
7. **Estimated tax position** — a real worksheet's stored numbers if one
   exists for the quarter (`worksheet.latest_worksheet_for()`), otherwise
   `preview()`'s live estimate, labeled "Current Estimate," never both at
   once.

## Why panel 6 doesn't call `retrieve()`

`EvidenceSpine.retrieve()` writes a real `audit_log` row on every call,
success or not, and on a hash mismatch creates a real urgent Queue item
— fine for a one-record detail page (the pattern Lane B's Queue detail
page already uses), not for a dashboard listing every fuel record's
evidence at once: every page view would write one audit row per record
shown. This is the same class of dashboard-viewing side effect already
found and excluded for `broken_evidence_linkage` in Category 2 Live
Indicators. Panel 6 reads `document_type`/`archive_path`/`file_hash`
straight from `evidence_records` instead — real, stored values, no
re-verification, no audit trail from merely viewing.

## The rate table version gap

`preview()` requires a `rate_table_version`, and there's no global
"current" one — multiple can coexist per quarter. Rather than guess,
`_tax_position()` checks how many distinct `source_version`s exist for
the quarter/fuel_type: exactly one is used automatically; zero shows "no
rate entered yet"; more than one shows "ambiguous, resolve via a real
build" — never silently picked, matching `IFTA_CONSTITUTION_v1`'s
no-fabrication rule for `MissingRateError`.

## Prepare This Quarter / Submit for Approval (`prepare.py`)

Added 2026-08-04 (Phase 5, modified from the blueprint's original
three-step design) — the app's first two write actions, kept in their
own module so `dashboard.py` stays exactly as read-only as it always
was. Three distinct stages, three distinct actions, by direction:

1. **Preparation** — `POST /prepare` → `prepare_quarter()`: the real
   `WorksheetEngine.build()` then the real `run_all_detectors()`, in
   sequence. Real persistence, real Category 1 exceptions, real
   exception Queue items. **Never submits for approval.**
2. **Review** — no code, no new artifact. The moment preparation
   succeeds, the dashboard already shows the real worksheet and its real
   exceptions the next time it's read — the dashboard *is* the review
   package, assembled live.
3. **Approval Routing** — `POST /submit` → `submit_quarter_for_approval()`:
   a deliberately separate action, calling only `submit_for_approval()`.
   Refuses if nothing's been prepared yet, or if this worksheet was
   already submitted — never creates a second approval Queue item.

Neither action ever reaches `attempt_seal()` — sealing a worksheet stays
exactly where it already was, reachable only after a real Queue
approval, unchanged by this module. Checked by `ast`-parsed import tests
across the whole package, not just this docstring's promise.

## Recommended Payment Amount (`recommend.py`)

Added 2026-08-04 (Phase 6's first named package —
`IFTA_CLERK_BLUEPRINT_v1.md` section 13: "a prepared DocuSign package, a
drafted accounting notification, a recommended payment amount —
proposals, never live sends"). The other two remain named-only,
undesigned — no DocuSign integration and no accounting/QuickBooks
integration exist anywhere in this codebase to design against.

Applies only to a real, **sealed** worksheet, matching section 2's
"after sealing" placement. `POST /recommend-payment` →
`generate_payment_recommendation()`: wraps the sealed worksheet's
already-approved `total_net_tax` in a recommendation label
(`remit`/`credit`/`no_payment_due`) and writes exactly one JSON file to
`ARCHIVE\IFTA\<quarter>\<id>_payment_recommendation.json` — the same
root `attempt_seal()` already writes its own sealed bundle to. No new
number is invented, no database write happens at all (the function's
only connection parameter is `read_only_conn`), and no payment API, bank
integration, or accounting write exists anywhere in this codebase for it
to reach — generating the recommendation is the entire action.
Idempotent: a worksheet that already has one returns it rather than
regenerating, since the sealed numbers it's built from can never change.

## Mileage Entry (`dispatch.ifta.mileage`)

Added 2026-08-05, resolving `IFTA_CLERK_BLUEPRINT_v1.md` section 12's
open question 2 ("is manual entry acceptable as the ongoing source of
truth indefinitely?") — yes, permanently. There is no ELD/GPS/odometer-
device integration anywhere in this codebase, and none is planned; this
was already decided twice before this route existed (the original
DispatchPilot direction, restated unchanged in the blueprint's section
3) — this app just gives that standing decision a real front door
instead of leaving mileage entry as the one CLI-only write action in an
otherwise browser-driven workflow (flagged directly in
`docs/pilot/DISPATCH_PILOT_RUN_2_REPORT_v1.md`'s findings).

`POST /record-mileage` → `dispatch.ifta.mileage.record_mileage()` — the
same real write `tools/mileage_worksheet.py` already used, moved out of
the tool so neither duplicates the `INSERT`; the CLI is now a thin
wrapper around it, unchanged in behavior. The entry itself is never
refused for implausibility — mileage is a human's own attestation, and
this route doesn't get to reject it — but after a successful write it
computes a live, rate-independent estimate
(`worksheet.live_fleet_mpg_estimate()`, sharing the exact aggregation
`build()`/`preview()` already use) and shows a non-blocking warning if
it would fall outside `exceptions.DEFAULT_MPG_BAND` — the same band the
`fleet_mpg_out_of_band` detector already checks, just surfaced earlier,
at entry time, instead of only after a full worksheet build. This
directly targets the real, twice-observed operational risk both pilot
runs found: manual mileage is "this system's one input with no
independent cross-check."

## Doctrine, restated as commitments for this app specifically

Updated 2026-08-04, first for `prepare.py`'s two write actions, then for
`recommend.py`'s, then 2026-08-05 for `record_mileage_route`'s — each
update corrects the section rather than leaving an earlier, now-
inaccurate version in place:

- **Evidence First** — every number is read exactly as Lane C's router
  already computed it; nothing here re-derives or second-guesses it.
  `prepare_quarter()` calls the same real `build()`/`run_all_detectors()`
  every prior IFTA build already used, and `generate_payment_recommendation()`
  wraps the sealed worksheet's own already-approved `total_net_tax` —
  neither computes a second, competing number.
- **Read-only Workspace** — no new table, no duplicate store, no direct
  `INSERT`/`UPDATE`/`DELETE` anywhere in this package's own source
  (checked by source scan in tests) — `dashboard.py` itself remains
  fully read-only; the write actions call existing, already-governed
  Lane C/Lane B functions, or write a single file to Archive, never a
  new database write path.
- **Human Authority** — Preparation, Submission, generating a payment
  recommendation, and recording mileage are each a distinct, deliberate
  human action, never bundled or automatic; `attempt_seal()` is
  unreachable from this app entirely, checked structurally (`ast`-parsed
  imports, not just this docstring's promise) — sealing a worksheet
  still requires the same real Queue approval it always did. Mileage
  entry stays entirely human-attested too — no device integration ever
  supplies or overrides a mileage figure, and the plausibility warning
  never refuses an entry, only flags it.
- **Recommendation Packages Only / no QuickBooks / no DocuSign / no
  Filing** — the recommendation *is* the deliverable now, not just a
  future placeholder: `generate_payment_recommendation()` writes a
  proposal to Archive and stops there — no payment API, bank
  integration, DocuSign, or QuickBooks write exists anywhere in this
  app for it to call.

See `docs/ifta-clerk/REVIEW_DASHBOARD_NOTES_v1.md`,
`docs/ifta-clerk/PREPARE_THIS_QUARTER_NOTES_v1.md`,
`docs/ifta-clerk/PAYMENT_RECOMMENDATION_NOTES_v1.md`, and
`docs/ifta-clerk/MILEAGE_ENTRY_NOTES_v1.md` for the full build record,
findings, and test coverage.

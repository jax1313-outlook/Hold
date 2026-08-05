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

## Doctrine, restated as commitments for this app specifically

Updated 2026-08-04 for `prepare.py`'s two write actions — the earlier
"nothing here writes anywhere" version of this section is no longer
literally true and is corrected below, not left stale:

- **Evidence First** — every number is read exactly as Lane C's router
  already computed it; nothing here re-derives or second-guesses it, and
  `prepare_quarter()` calls the same real `build()`/`run_all_detectors()`
  every prior IFTA build already used — no second computation path.
- **Read-only Workspace** — no new table, no duplicate store, no direct
  `INSERT`/`UPDATE`/`DELETE` anywhere in this package's own source
  (checked by source scan in tests) — `dashboard.py` itself remains
  fully read-only; the two write actions call existing, already-governed
  Lane C/Lane B functions instead of writing anything new.
- **Human Authority** — Preparation and Submission are two distinct,
  deliberate human actions, never bundled or automatic; `attempt_seal()`
  is unreachable from this app entirely, checked structurally
  (`ast`-parsed imports, not just this docstring's promise) — sealing a
  worksheet still requires the same real Queue approval it always did.
- **Recommendation Packages Only / no QuickBooks / no DocuSign / no
  Filing** — still true: `prepare_quarter()`/`submit_quarter_for_approval()`
  only ever write to this system's own governed tables (`ifta_worksheets`,
  `ifta_exceptions`, `queue_items`); no external system integration
  exists anywhere in this app.

See `docs/ifta-clerk/REVIEW_DASHBOARD_NOTES_v1.md` and
`docs/ifta-clerk/PREPARE_THIS_QUARTER_NOTES_v1.md` for the full build
record, findings, and test coverage.

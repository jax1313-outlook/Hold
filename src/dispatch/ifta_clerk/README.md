# dispatch.ifta_clerk — the Review Dashboard

The primary user experience of the IFTA Clerk
(`docs/ifta-clerk/IFTA_CLERK_BLUEPRINT_v1.md` section 7, approved
2026-08-04). One screen, one quarter, one fuel type, assembled entirely
from real, already-governed sources — no new table, no new writer, no
duplicate store.

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

## Doctrine, restated as commitments for this app specifically

- **Evidence First** — every number is read exactly as Lane C's router
  already computed it; nothing here re-derives or second-guesses it.
- **Read-only Workspace** — no `INSERT`/`UPDATE`/`DELETE` anywhere in
  this package (checked by source scan in tests).
- **Human Authority** — no route approves, seals, resolves, or builds
  anything; every write action is a plain link out to the real Queue or
  `/ifta`'s own write routes.
- **Recommendation Packages Only / no QuickBooks / no DocuSign / no
  Filing** — trivially true: nothing here writes anywhere, so there's no
  external system to integrate with yet.

See `docs/ifta-clerk/REVIEW_DASHBOARD_NOTES_v1.md` for the full build
record, findings, and test coverage.

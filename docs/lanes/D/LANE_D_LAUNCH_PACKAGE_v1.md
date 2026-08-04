# LANE D LAUNCH PACKAGE — Reports Layer

Purpose: a launch-ready build packet for Lane D, current as of commit
`778ddde` on `integration` (Lanes A, B, and C merged). Supersedes Packet D
in `docs/reference/DISPATCH_MATRIX_EXECUTION_PACKAGE_v1.md` — see §9.
Repository: `jax1313-outlook/hold`, branch `build/reports`.
Authority: Mike Zachary is final authority. This document contains no
implementation code and does not itself open a build session.

---

## 1. Mission

Build the deterministic answer surface of Dispatch — a layer, not an
agent. Reports reads governed storage and writes nothing but the print
queue. For the person using it, this screen *is* Dispatch: the two bright
lines (`REPORTS_CHARTER_v1.md`) are non-negotiable — read-only except one
narrow writer, and arithmetic yes, domain judgment never. If a number
could ever differ between the Reports screen and the owning agent's own
record, the design has failed.

## 2. Files to create

All new files. Nothing in this list exists yet (`src/dispatch/reports/**`
and `tests/lane_d/**` currently hold only `.gitkeep` placeholders).

**`src/dispatch/reports/`**
- `readonly.py` — this lane's own `mode=ro` SQLite connection opener (the
  same technique `dispatch.ifta.readonly` uses, duplicated rather than
  imported — see §4 on why).
- `templates.py` — the template engine: loads a report definition (query
  + layout) from a versioned JSON file under `LIBRARY\Templates\Reports\`;
  rendering a template against data + an as-of timestamp must produce
  identical bytes for identical inputs, always.
- `queries.py` — the actual SQL each report type runs against the
  read-only connection: aggregate/group-by only, never a computed tax
  value, never a reclassification.
- `reports/fuel_spend.py`, `reports/expense_summary.py`,
  `reports/ifta_position.py` — one module per report type, each a thin
  wrapper choosing filters and calling `queries.py`. `ifta_position.py`
  reads `ifta_worksheets`/`ifta_worksheet_lines` values as stored,
  full stop — no arithmetic on them beyond formatting.
- `snapshot.py` — the *only* writer in this lane: Save For Printing
  writes an immutable HTML snapshot to `ARCHIVE\ReportSnapshots\YYYY\`
  (template version + as-of stamped) and a `print_queue` row referencing
  it. Uses a normal read-write connection (via `dispatch.common.db.bootstrap`
  and its own schema install — see §4), never the read-only one.
- `app.py` — Flask UI: Recents chips (last three runs), Report Type /
  six date-range presets / context-sensitive Filter (Truck if fleet > 1,
  State on Fuel/IFTA, Category on Expenses — **no Sort By**), a big-number
  visual answer with a comparison line, a below-the-fold breakdown, a
  freshness line with pending-review count (from `queue_items`), and a
  Save For Printing action. Print stylesheet.
- `templates/` (Flask/Jinja templates), `static/` — tablet-friendly, same
  conventions Lane B's UI already established.
- `README.md` — documents the template engine, the read-only/single-writer
  split, and how a new report type is added (template file + fixture,
  zero code change to the engine).

**`library_seed/Templates/Reports/`** — the actual template JSON files:
`fuel_spend.v1.json`, `expense_summary.v1.json`, `ifta_position.v1.json`
(installed to Library by the existing `tools/seed_library.py` — no
changes needed there).

**`tests/`**
- `tests/lane_d/**` — the full Lane D test suite (§6).
- `tests/fixtures/**` — fixture data conforming to the frozen schemas,
  plus a fixture README (§9 on the D1 cross-link note, now moot but
  worth stating plainly).

## 3. Files to modify

- `docs/lanes/D/NOTES.md` — update at the end of the session, explicitly
  recording the deferred final-fidelity-gate item (§7) as open, not
  skipped.

Nothing else. `contracts/**`, `docs/governance/**`, every other lane's
directory, and `src/dispatch/{common,evidence,queue,receipt,ifta}/**` are
forbidden **to write to** — see §4 for what "forbidden" does and doesn't
mean for this lane specifically, since it differs from how Lanes B and C
related to their upstream dependencies.

## 4. Dependencies

- Contracts 1.1 (Evidence — read-only, for freshness/context only), 1.6
  (Audit). In-force schema fields on `fuel_records`, `expense_records`,
  `mileage_records`, `ifta_worksheets`, `ifta_worksheet_lines`,
  `queue_items` — all real tables now, not draft.
- **What "forbidden files" means for this lane, precisely.** Packet D's
  forbidden list names `src/dispatch/{common,evidence,queue,receipt,ifta}/**`
  as a block — broader than Lane B's or Lane C's own forbidden lists,
  which named only the specific lanes each depended on. Read literally as
  "no imports at all," this would make gate 4 (audit entries for
  snapshot/save actions) impossible, since the shared audit writer lives
  in `dispatch.common.audit`. The consistent reading, matching how every
  other lane has actually used this phrase (Lanes B and C both imported
  Lane A's and each other's real modules freely, "forbidden" meaning
  *never create or edit a file under that path*): Lane D **may import**
  `dispatch.common.db.bootstrap`, `dispatch.common.audit`, and
  `dispatch.common.ids` — its one legitimate shared dependency — but
  **must not** import business logic from `evidence`, `queue`, `receipt`,
  or `ifta`. It has no need to: Reports never calls
  `EvidenceSpine.retrieve()` or `QueueStore.create()`, it reads their
  tables directly via SQL through its own read-only connection. This is
  actually the more literal reading of "Reports reads governed storage
  only" — SQL reads against tables, not API calls into other lanes'
  logic — and it's why `readonly.py` is duplicated here rather than
  imported from `dispatch.ifta.readonly`: importing anything from
  `dispatch.ifta` at all would blur exactly the line this lane exists to
  keep sharp. If this reading turns out to be wrong, it's a one-line fix
  in `NOTES.md`, not a rearchitecture.
- Fixture data (§9 on why this lane's own build session can do better
  than Packet C-era fixtures) plus the deferred real-data fidelity gate.

## 5. Contract references

| Contract | File | Status | Relevance to Lane D |
|---|---|---|---|
| Evidence Record | `contracts/evidence_record.schema.json` | FROZEN v1.0 | Read-only, for freshness context only |
| Audit Entry | `contracts/audit_entry.schema.json` | FROZEN v1.0 | Every snapshot/save action writes one |
| Fuel Record | `contracts/fuel_record.schema.json` | FROZEN v1.0 | Fuel Spend report's source table |
| Expense Record | `contracts/expense_record.schema.json` | FROZEN v1.0 | Expense Summary report's source table |
| Expense Vocabulary | `contracts/expense_vocabulary.schema.json` | FROZEN v1.0 | Expense Summary's Category filter values |
| Mileage Record | `contracts/mileage_record.schema.json` | FROZEN v1.0 | Context for freshness/Cost Per Mile (v1.1, not this lane) |
| Queue Item | `contracts/queue_item.schema.json` | FROZEN v1.0 | Pending-review count on the freshness line |

Lane D never validates against or writes `fuel_records`/`expense_records`
schemas — it only reads them. No new record-producing contract is owned
by this lane.

## 6. Test requirements

Per `DISPATCH_BUILD_BLUEPRINT_v1` Section 5 and Packet D's validation
gates:

1. **Conformance** — fixture data validates against the in-force schemas
   before any report runs against it (garbage fixtures would make every
   other gate meaningless).
2. **Golden regression:**
   - **Determinism** — identical inputs (same template version, same
     as-of timestamp, same underlying data) produce byte-identical
     output, repeated.
   - **Fidelity** — every displayed total equals independent SQL
     arithmetic computed separately from the report code, over the same
     fixtures.
   - **IFTA display-only** — IFTA Position's numbers match the stored
     `ifta_worksheets`/`ifta_worksheet_lines` fixture values exactly,
     never recomputed by this lane.
   - **Snapshot-on-save** — correct template-version + as-of stamps;
     the print queue holds a reference, never a second copy of the data.
   - **Queue-clear never touches the Archive copy** — clearing a
     `print_queue` entry (a status transition, not a `DELETE` — see §10
     risk #1) leaves the snapshot file in `ARCHIVE\ReportSnapshots\`
     untouched.
3. **Boundary refusal (negative tests):**
   - Any write attempt through the read-only connection fails
     (`sqlite3.OperationalError`), against *any* table — same proof
     technique Lane C's `WorksheetEngine` used.
   - No tax math, rate table, or recomputation of any stored IFTA value
     anywhere in this lane — verified by test *and* by grep (same
     pattern as every other lane's immutability checks, applied here to
     "no arithmetic on domain-computed values" instead of "no
     UPDATE/DELETE").
   - No report type renders without complete fixture data behind it.
4. **Audit completeness** — every snapshot/save action writes a
   well-formed audit entry.

## 7. Acceptance criteria (Definition of Done)

- All Lane D tests green, including every negative test in §6.
- Conformance suite (extended, not duplicated) green.
- `src/dispatch/reports/README.md` written.
- `docs/lanes/D/NOTES.md` updated: built / flagged / deliberately not
  built, **explicitly recording the deferred final-fidelity gate** (see
  below) as an open item — never silently dropped.
- **Mike's walkthrough**, run per `docs/reference/WALKTHROUGH_PROCEDURE_v1.md`:
  "fuel today" answered in one glance on a tablet-sized screen over LAN
  in sandbox; a save-for-print round trip.
- **Docs match as-built.**
- Branch `build/reports` ready for `integration` (merges last).
- **Deferred gate, explicit per `REPORTS_CHARTER_v1.md`:** final report
  fidelity — every displayed total equals independent SQL arithmetic —
  re-run against **real** Lane C output on `integration`, not just
  fixtures, before this lane's merge is considered complete. §9 notes
  this lane's own build session is now well-positioned to satisfy this
  directly rather than defer it further, since Lane C has already
  merged — but that's a recommendation for the build session, not a
  redefinition of the gate itself.

## 8. Expected deliverables

Working `dispatch.reports` package (template engine, three report types,
Flask UI, snapshot/print-queue writer); `fuel_spend.v1.json`,
`expense_summary.v1.json`, `ifta_position.v1.json` seeded to Library;
fixtures + fixture README; Lane D tests green; `NOTES.md`; branch
`build/reports` ready for `integration`.

**Forbidden files:** `contracts/**` (read-only) · `docs/governance/**` ·
`src/dispatch/{evidence,queue,receipt,ifta}/**` business logic (query
their tables directly instead — see §4) · `src/dispatch/common/**` as an
edit target (importing `bootstrap`/`audit`/`ids` from it is fine and
expected) · production config · any Expense Summary artifact that
invents a category outside the frozen vocabulary · anything outside this
repository.

**Must not:** any DB write outside the single snapshot/print-queue
writer (prove with a negative test); any tax math, rate table, or
recomputation of a stored IFTA value; any report type shipped without
complete data behind it; `localStorage` or client state that changes
displayed numbers; PDF generation; a Sort By control; scope expansion
beyond Fuel Spend, Expense Summary, and IFTA Position.

## 9. What changed since Packet D was written

Packet D (2026-08-03) scoped this lane against a system where #3 was
held and Lane C didn't exist yet. Both are different now:

1. **Expense Summary is unblocked.** #3 (closed expense vocabulary) was
   APPROVED AS WRITTEN 2026-08-04. `REPORTS_CHARTER_v1.md` already
   reflects this: Expense Summary's Category filter and fixtures "may
   now be built against the frozen `contracts/expense_vocabulary.schema.json`...
   **Not yet built** — no Lane D session has run." A session reading only
   the old Packet D text would treat Expense Summary as still blocked and
   build a two-report v1 (Fuel Spend, IFTA Position) instead of the
   three-report v1 that's actually authorized.
2. **Lane C has merged into `integration`.** Packet D was written when
   Lane D's dependency on Lane C was necessarily fixture-only, with a
   *deferred* final-fidelity gate "re-run against real Lane C data on
   integration before merge 5." That data now exists — for real, in this
   repository, on the branch this launch package's session forks from.
   This doesn't change the charter's gate (§7 still lists it, explicitly,
   per the charter's own "never silently skipped" instruction) — but it
   means a Lane D build session can construct its fixtures **by actually
   running Lane A's `EvidenceSpine.register()` and Lane C's
   `Router.route_line()`** against sandbox data, the same technique this
   session used for its own smoke tests, rather than hand-typing fixture
   SQL rows that merely *conform* to the schema shape. That produces
   fixtures with genuine referential and arithmetic integrity from the
   real pipeline, substantially de-risking the deferred gate rather than
   leaving it purely for later. Recommended, not required — flag in
   `NOTES.md` if a different approach is taken and why.
3. **The fuel fixture D1-cross-link hedge is moot.** Packet D's old build
   prompt said fuel fixtures "must not presuppose or exclude the D1
   cross-link" because #2 was undecided. #2 is approved;
   `expense_record_id` is a real, required, frozen field on `FuelRecord`.
   Fixtures (or, per point 2, real routed records) naturally carry it.

## 10. Risks

1. **Clearing the print queue vs. "no worker deletes anything, anywhere,
   ever."** `DISPATCH_BASE_CONSTITUTION_v1` #6 is a blanket, unqualified
   rule. `DISPATCH_REPORTS_DESIGN_REVIEW_v1` Section 5 just as plainly
   describes `print_queue` entries as disposable and clearable — "custodian:
   the layer itself, contents disposable." Read together, the doctrines
   don't actually conflict once `print_queue` is understood correctly:
   #6 protects *governed records* (evidence, financial records, the audit
   trail) — the substantive things the whole system exists to protect.
   `print_queue` holds nothing but *references* to already-immutable
   Archive snapshots; losing a reference destroys no data, since the real
   artifact stays permanently in `ARCHIVE\ReportSnapshots\`. This launch
   package resolves it the conservative way rather than by asserting that
   reading and hoping it's right: **`print_queue` gets the same treatment
   Lane B gave `queue_items`** — a `status` column
   (`queued`/`printed`/`cleared`), no `DELETE` code path at all, ever.
   "Clearing" is a status transition, identical in shape to every other
   lane's approach, and the constitutional question never has to be
   litigated because no delete is ever attempted. If a future session
   decides a real `DELETE` is actually required, that's a new decision to
   record, not an assumption to make here.
2. **Trust is single-use** (`DISPATCH_REPORTS_DESIGN_REVIEW_v1` risk #1).
   The first wrong or half-empty number on this screen costs adoption of
   the whole platform, because for this audience the Reports screen *is*
   Dispatch. Mitigation: never ship a report type without complete
   fixture (or real) data behind it; always show the freshness line and
   pending-review count; show IFTA's exception count inline, never hide
   it to make the screen look cleaner.
3. **Divergent numbers** (design review risk #3). If Reports ever
   recomputes anything an agent already computed, two screens will
   eventually disagree and both lose credibility — this is why
   `ifta_position.py` must read `ifta_worksheets` values as stored, full
   stop, with a dedicated test proving no arithmetic happens on them
   beyond formatting/display.
4. **The side-door risk** (design review risk #4). Any accidental write
   path is an ungoverned output channel. The read-only/single-writer
   split needs its own negative test, not just an absence of `INSERT`
   statements in the code someone happened to write.
5. **Stale snapshots resurfacing as truth** (design review risk #5). The
   template-version + as-of stamp on every printed page is what settles
   a "this doesn't match what I'm looking at now" argument. Don't treat
   the stamp as decorative — test that it's actually correct, not just
   present.

## 11. Rollback plan

`build/reports` currently contains nothing beyond what it shares with
`integration` (Lanes A, B, and C, merged) — there is no Lane D-specific
work to lose yet.

If a Lane D session needs to be abandoned or restarted:

1. Before abandoning, write whatever is known to `docs/lanes/D/NOTES.md`.
2. `git reset --hard` (or re-branch) `build/reports` back to
   `integration`'s current tip — discards only Lane D's in-progress work.
3. Delete any sandbox directories the aborted session created on disk —
   outside the repository, outside version control.
4. No `integration`/`main` rollback needed unless a Lane D merge *had
   already happened* — not applicable yet. Lane D merges last, so a
   rollback here is the lowest-blast-radius of any lane's by definition.

## 12. Ready-to-run build prompt

```
You are building LANE D of Dispatch Matrix Group 1 in the Hold repository,
branch build/reports. You are a bounded build session. Reports is a LAYER,
not an agent: it reads governed storage and writes nothing but the print
queue. Its numbers must never be wrong -- for the user, this screen IS
Dispatch.

STATUS (2026-08-04): all 14 approval items are APPROVED. Lanes A, B, and C
have MERGED into integration -- this branch's history already contains
all three. #3 (closed expense vocabulary) being approved means Expense
Summary is IN SCOPE for this lane now, unlike the old Packet C-era
Packet D text -- build three report types (Fuel Spend, Expense Summary,
IFTA Position), not two. Read REPORTS_CHARTER_v1.md directly; do not rely
on the old packet's BLOCKED section, which is stale.

READ FIRST: docs/lanes/D/LANE_D_LAUNCH_PACKAGE_v1.md in full;
docs/governance/REPORTS_CHARTER_v1.md;
docs/reference/DISPATCH_BUILD_BLUEPRINT_v1.md Parts 1, 3, 4.4, 5;
docs/reference/DISPATCH_REPORTS_DESIGN_REVIEW_v1.md Sections 2, 3, 5, 6;
contracts/fuel_record.schema.json, expense_record.schema.json,
expense_vocabulary.schema.json, queue_item.schema.json, audit_entry.schema.json;
docs/reference/WALKTHROUGH_PROCEDURE_v1.md.

BUILD (src/dispatch/reports/): a template engine -- report = versioned
JSON template (query + layout) from LIBRARY\Templates\Reports\; rendering
= template version + as-of timestamp + data; identical inputs must
produce identical bytes, always (this is what makes adding a report type
later a template file + fixture, zero code change). Three report types:
Fuel Spend, Expense Summary (Category filter against the frozen closed
vocabulary), and IFTA Position (reads STORED ifta_worksheets/
ifta_worksheet_lines values only, labeled "Prepared -- estimate, not
filed", exception count inline -- no recomputation, ever). Flask UI:
Recents chips (last three runs); Report Type / Date Range (Today,
Yesterday, This Week, This Month, Last Month, Custom) / context-sensitive
Filter (Truck only if fleet>1, State on Fuel/IFTA, Category on Expenses)
-- NO Sort By. Visual answer: one big number readable at arm's length,
secondary figure beneath, one comparison line, breakdown below the fold,
freshness line with pending-review count (from queue_items). Save For
Printing: immediate immutable HTML snapshot to ARCHIVE\ReportSnapshots\YYYY\
stamped with template version + as-of; print_queue holds a REFERENCE with
a status column (queued/printed/cleared) -- no DELETE code path, ever, on
print_queue (see launch package risk #1: this is a deliberate, considered
choice, not an oversight). Print stylesheet. DB opened READ-ONLY (mode=ro,
this lane's own readonly.py, not imported from dispatch.ifta) everywhere
except the single snapshot/print-queue writer, which may import
dispatch.common.db.bootstrap, dispatch.common.audit, and
dispatch.common.ids -- but nothing from dispatch.{evidence,queue,receipt,ifta}.
Read those lanes' tables directly via SQL instead.

Build fixtures (tests/fixtures/**) by actually running Lane A's
EvidenceSpine.register() and Lane C's Router.route_line() against sandbox
data where practical, not just hand-typed rows conforming to the schema
shape -- Lane C is real and merged now, so this lane can substantially
de-risk the charter's deferred real-data fidelity gate directly.

MUST NOT: any write outside the single writer (prove with a negative
test); any tax math, rate table, or recomputation of stored IFTA values;
any report type without complete data behind it; localStorage or client
state that changes numbers; PDF generation; a Sort By control; editing
contracts/ or any other lane's code; scope expansion.

DONE WHEN: determinism test green (identical inputs -> identical bytes,
repeated); fidelity test green (displayed totals = independent SQL
arithmetic on the same fixtures); IFTA display-only test green;
read-only enforcement test green (negative test, any table); snapshot
stamps verified; fast on a tablet-sized viewport over LAN in sandbox;
conformance green; docs/lanes/D/NOTES.md written, explicitly recording
the deferred real-Lane-C-data fidelity gate as open (not skipped) even
if this session's fixtures were built from real pipeline output; branch
ready (merges LAST). Mike's walkthrough ("fuel today" in one glance,
save-for-print round trip) still required before merge.
```

---

*End of LANE_D_LAUNCH_PACKAGE_v1. Documentation only; no implementation
code; does not itself open a build session.*

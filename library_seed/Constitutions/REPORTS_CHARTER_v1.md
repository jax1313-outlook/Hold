# REPORTS_CHARTER_v1

**Status:** Fully adopted (bright lines, and now Expense Summary is
authorized). Reports is a layer, not an agent — it has a one-page
charter, not a constitution. Operates under `CONSTITUTION.md` and
`DISPATCH_BASE_CONSTITUTION_v1.md`. Required before Lane D.

## The two bright lines

Settled three times across the audit series
(`DISPATCH_ARCHITECTURE_AUDIT_v1` Q13, `DISPATCH_REPORTS_DESIGN_REVIEW_v1`
Q1/Q11, `DISPATCH_FINAL_PRECODING_REVIEW_v1` Q6):

1. **Reports reads governed storage only, and writes nothing except the
   print queue.** Database connection opened READ-ONLY (`mode=ro`)
   everywhere except one narrow print-queue/snapshot writer. Any other
   write attempt must fail — write the negative test.
2. **Arithmetic yes, domain judgment never.** Reports may sum, average,
   count, and group-by over stored records. It may never compute tax,
   classify, apply accrual logic, or reclassify anything on the fly.
   Domain-computed values — IFTA tax positions above all — are computed
   once by the owning agent, stored, and merely displayed. **The test:
   if a number could ever differ between the Reports screen and the
   owning agent's worksheet, the design has failed.**

Reports must be deterministic: same question, same data, same answer,
every time. An agent (with judgment) is the wrong shape for this layer.

## A report is a snapshot, never a source of truth

Live answers are ephemeral — ask again, get freshly-regenerated numbers.
Saving writes an immutable, dated snapshot to Archive immediately (stamped
with template version + as-of timestamp); the print queue holds a
*reference* to that snapshot, never a second copy. Clearing the queue
never touches the Archive copy. Nobody cites last month's snapshot as
authority.

## Templates are Library data, not code

A report = a versioned JSON template (query definition + layout) loaded
from `LIBRARY\Templates\Reports\`, Librarian custody. Rendering = template
version + as-of timestamp + data. Identical inputs must produce identical
bytes, always. This is also why adding a report type is a template file +
fixture, not a code change — the engine must be built so that holds.

## v1 scope (Lane D)

Per `DISPATCH_MATRIX_EXECUTION_PACKAGE_v1` Packet D and
`DISPATCH_BUILD_BLUEPRINT_v1` Part 4.4: **Fuel Spend** and **IFTA
Position** (reads stored `ifta_worksheets` values only, labeled
"Prepared — estimate, not filed," exception count inline) over fixture
data conforming to the frozen schemas. Flask UI: Recents chips (last
three runs), Report Type / six date-range presets / context-sensitive
Filter (Truck if fleet > 1, State on fuel/IFTA) — **no Sort By**.
Big-number visual answer, comparison line, below-the-fold breakdown,
freshness line with pending-review count. Save For Printing → immediate
immutable HTML snapshot + print-queue reference; print stylesheet.

**Expense Summary — unblocked, 2026-08-04 (#3 approved as written):** the
category filter and fixtures may now be built against the frozen
`contracts/expense_vocabulary.schema.json`. If the template engine was
built so a new report type is a template file + fixture, this should
require zero code change to the engine itself. **Not yet built** — no
Lane D session has run.

**Fuel fixture note (D1, resolved):** the D1 cross-link (#2, approved) is
now a real, frozen field (`expense_record_id` on FuelRecord). Fuel
fixtures built going forward may include it; it is no longer an open
question to hedge against.

## Deferred gate

Final report fidelity — every displayed total equals independent SQL
arithmetic on the same data — is re-run against **real** Lane C output on
`integration` before merge 5. Fixture-based fidelity in Lane D's own gate
is necessary but not sufficient; this is recorded as an explicit open
item, never silently skipped.

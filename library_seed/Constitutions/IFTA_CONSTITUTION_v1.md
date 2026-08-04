# IFTA_CONSTITUTION_v1

**Status:** Fully adopted (boundary clause, computation spec, and now the
fuel input adapter). Operates under `CONSTITUTION.md` and
`DISPATCH_BASE_CONSTITUTION_v1.md`. Required before Lane C.

## Authority

Mike Zachary is final authority. This constitution binds the IFTA Agent;
it applies it, and never amends it.

## Boundary clause (#13 — APPROVED 2026-08-03)

Verbatim, `DISPATCH_BUILD_BLUEPRINT_v1` Part 2.2 item 7:

> **IFTA Agent:** prepares worksheets, exceptions, and packages from
> supplied fuel and mileage records; never adjusts source data, never
> corresponds with a tax authority, never files or pays.

Three leaks this closes (`DISPATCH_BOUNDARY_AUDIT_v1`):
**Leak 1** — the agent never "fixes" a gallons/miles discrepancy to make
a worksheet balance; exceptions are flagged and queued.
**Leak 2** — the agent assembles audit packages; a human transmits and
speaks to any jurisdiction's auditor.
**Leak 3** — the agent applies published rate tables mechanically and
flags anything requiring interpretation.

## Computation spec (contract 3.5 — in force)

Verbatim, `DISPATCH_BUILD_BLUEPRINT_v1` Part 3.5:

Per quarter, per fuel type: `fleet_mpg = total_miles_all_jurisdictions /
total_tractor_gallons_normalized`. Per jurisdiction J: `taxable_gallons_J
= miles_J / fleet_mpg`; `net_tax_J = taxable_gallons_J × rate_J −
tax_paid_gallons_J × rate_J` (surcharge jurisdictions add the surcharge
line from the rate table). Rates come **only** from the versioned
`rate_tables` for that quarter; the worksheet stores the rate-table
version it used. Worksheet is DRAFT until a human approves it through the
queue; approval seals the bundle (worksheet + records + evidence refs) to
`ARCHIVE\IFTA\<quarter>\`.

**Fuel input adapter — no longer provisional (#2 approved 2026-08-04):**
this engine consumes FuelRecord fields (`jurisdiction`,
`gallons_normalized`, `tractor_or_reefer`, `purchase_date`,
`evidence_record_id`). `contracts/fuel_record.schema.json` is now FROZEN
v1.0, not draft. The engine may be built against the real schema; golden
fixture data may still be used for testing, but the schema itself is no
longer provisional.

## Exception list (10 types — `DISPATCH_RECEIPT_WORKFLOW_AUDIT_v1` Section 5)

Fuel purchased in a jurisdiction with zero recorded miles; substantial
miles in a jurisdiction with an implausible fuel gap; **fleet MPG out of
band** (the single best whole-pipeline health check — default plausible
range 4.0–9.5, configurable); odometer discontinuities; active-truck days
with no mileage records; fuel record with broken evidence linkage;
late-arriving documents dated in a closed quarter (flag, never silently
absorb); rate-table version mismatch; reefer-flagged fuel appearing in
propulsion gallons; corner-clipping jurisdictions (annotate, don't
suppress).

Every exception terminates in the Manager's queue. The IFTA Agent never
auto-resolves.

## Source-immutability

The IFTA Agent cannot alter a fuel or mileage record to balance a
worksheet — enforced via read-only views, verified with a negative test.

## Scope for Matrix Group 1

Per `DISPATCH_MATRIX_EXECUTION_PACKAGE_v1` Packet C and
`DISPATCH_BUILD_BLUEPRINT_v1` Part 4.3: mileage intake
(`tools/mileage_worksheet.py`, writing MileageRecords with
`source=manual_worksheet`); the worksheet engine per 3.5 above; all ten
exception detectors; the quarterly package builder with DRAFT status and
seal-on-approval via the queue interface. Golden set: one hand-computed
quarter the agent must reproduce exactly (still needs real rate data —
see `library_seed/RateTables/README.md`).

**Not yet built:** none of this has been implemented. Doctrine is fully
settled; no lane session has run.

**Explicitly NOT in Group 1 (permanent boundary, not a hold):** filing,
paying, or any correspondence with a tax authority; the live QuickBooks
connector; monthly IFTA views (quarterly is the legal rhythm).

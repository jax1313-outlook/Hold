# RateTables

`DISPATCH_HOLD_SEED_PACKAGE_v1` §1/§5 calls for this directory to be
"seeded with the current IFTA quarter table + source note" as part of
commit S5.

**Not done — and deliberately not fabricated.** None of the source
documents provided to this seeding session (the eleven files in
`docs/reference/`) contain actual IFTA per-jurisdiction tax rate figures
for any quarter. Inventing tax rate numbers would violate
`CONSTITUTION.md` Rule 11 (No Fabrication — "Unknown means Unknown") and,
unlike most gaps in this seed, could cause real financial/compliance harm
if a real rate table were ever mistaken for this placeholder.

## What's actually needed here

Per `DISPATCH_BUILD_BLUEPRINT_v1` Part 3.3, a `rate_tables` row shape:
`jurisdiction, quarter, fuel_type, rate, source_version`. The IFTA
computation spec (Part 3.5) requires the worksheet engine to read rates
**only** from this versioned table, never hardcoded, and to record which
version it used.

## What must happen before Lane C's gate (not before Lane C starts)

Per the Hold Seed Package §7, golden sets — and by extension real rate
data — "may start empty; they must be non-empty before Lane C's *gate*,
not its start." Mike (or whoever holds the official quarterly IFTA rate
publication) supplies:

1. The actual per-jurisdiction, per-fuel-type rates for at least one real
   or hand-computed quarter (this doubles as the source for
   `tests/golden/ifta/`, the hand-computed golden quarter).
2. The source citation/version for that rate set (which official
   publication, which quarter, retrieved when).

Until then, Lane C may build the worksheet engine against
`rate_tables`-shaped **fixture** data it constructs itself for unit
testing — clearly marked as fixture, never presented as real rates — but
cannot pass its golden-regression gate (blueprint Part 5, gate 2) without
a real hand-computed quarter here.

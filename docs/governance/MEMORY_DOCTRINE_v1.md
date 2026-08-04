# MEMORY_DOCTRINE_v1

**Status:** Partially adopted. Operates under `CONSTITUTION.md` and
`DISPATCH_BASE_CONSTITUTION_v1`. Required before Lane A per
`DISPATCH_HOLD_SEED_PACKAGE_v1` §2/§6.

**Seeding note:** the tier definitions/mapping (#1) and lifecycle content
this document is supposed to carry live in `DISPATCH_BUILD_BLUEPRINT_v1`,
not provided to this seeding session. This document records only what is
actually stated in the two provided documents.

## Tier definitions and mapping (#1)

**STATUS: PENDING SOURCE.** Not described in either document provided to
this seeding session beyond the storage-mapping cross-reference in
`DISPATCH_BASE_CONSTITUTION_v1` #1.

## Lifecycle

**STATUS: PENDING SOURCE**, with the following states named in the
Execution Package and binding meanwhile:

- Evidence records: `register → retrieve / link_children`. No `update`,
  no `delete`, ever, on any path.
- Queue items: `open → in_review → approved / rejected / resolved`.
- Receipt line items: extraction terminates in a `pending_routing` state
  (validated, classified, full provenance) — held, awaiting the router.
- IFTA quarterly packages: `DRAFT → seal-on-approval` via the queue
  interface.

The general draft→candidate→approved→archived and
extracted→validated→consumed→sealed lifecycle pattern referenced by the
Hold Seed Package's description of this document is not itself detailed
in either provided document — do not assume its field-level meaning
without the blueprint.

## TRADE MEMORY — HELD (#14), reserved

This section is intentionally empty. #14 (Trade Memory doctrine) is an
open hold — see `docs/decisions/DECISION_LOG.md`. No pattern storage and
no pattern reliance exists anywhere in Dispatch Matrix Group 1 while this
section is empty. Every unknown format goes to the review queue; human
rulings accumulate in the audit trail and can seed patterns later. On
Mike's decision, Packet C-3 (Trade Memory) is issued, seeded from those
accumulated human rulings, before any journeyman certification.

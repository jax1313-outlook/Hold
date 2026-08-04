# Hold

Construction repository for Dispatch Matrix Group 1 (Librarian, Manager,
Receipt/IFTA, and Reports lanes). Seeded per `DISPATCH_HOLD_SEED_PACKAGE_v1`.

## What this is

A clean, intentionally-empty-at-seed construction repository. No build
session touches production `D:\` roots. Sandbox configuration only, until
Mike Zachary cuts over after merge 5.

## What this is not

- **Not** a clone of the live Dispatch system.
- **Not** the system of record. Archive is (per `CONSTITUTION.md` Articles
  III/VIII), and Archive lives outside this repository, in the sandbox
  roots named by `config/sandbox.config.json`.
- **Not** authorized to hold production config. `config/dispatch.config.json`
  must never exist here before cutover.

## Where the law lives

- `CONSTITUTION.md` (Level 1 Transport Inc. master constitution) is supreme
  law for all governed development work, per its own Article 0. It is
  maintained outside this repository (Copilot Workspace/Constitution per
  `CONTEXT_MASTER.md` §13) and is not duplicated here.
- `docs/governance/` holds the project-scoped constitutions and doctrines
  that operate *under* `CONSTITUTION.md`: `DISPATCH_BASE_CONSTITUTION_v1`,
  the per-worker constitutions/charters, `APPROVAL_REGISTER.md` (single
  source of truth for the 14 approval items), and `MEMORY_DOCTRINE_v1`.
- `contracts/` holds the frozen / draft / held-absent data contracts —
  read-only law to every lane. See `contracts/CONTRACT_REGISTER.md`.
- `docs/decisions/DECISION_LOG.md` tracks open holds.
- `docs/reference/` holds read-only copies of source planning documents.

## Binding rules (from `DISPATCH_MATRIX_EXECUTION_PACKAGE_v1`)

1. Frozen contracts are read-only law. A session that believes a contract
   is wrong records it in its lane `NOTES.md` and stops that thread — it
   never edits `contracts/`.
2. A session builds only inside its Allowed Files (see its packet in
   `docs/reference/`). Touching another lane's directories is a failed
   gate, even if the change is correct.
3. If work cannot proceed without a HELD decision (#2, #3, #4, #14), the
   session stops that thread, records the blockage in `NOTES.md`, and
   continues other in-scope work. It never assumes the decision.
4. Sandbox config only (`config/sandbox.config.json`); the config loader
   must refuse production roots in sandbox mode; no session ever creates a
   production config.
5. Every packet's session ends by writing/updating its lane
   `docs/lanes/<X>/NOTES.md`: what was built, what was flagged, what was
   deliberately not built.

## Branch discipline

```
main
 └── integration
      ├── build/librarian-spine   (Lane A — merges first)
      ├── build/manager-queue     (Lane B — merges after A)
      ├── build/receipt-ifta      (Lane C — merges after B; may itself wait on #2/#3)
      └── build/reports           (Lane D — merges last)
```

`main` accepts merges only from `integration`. `integration` accepts merges
only lane-by-lane, in that order, each after its six validation gates and
Mike's sign-off. The first merge into `integration` additionally waits on
#4 (Base Constitution hard-gate amendment — a document milestone, see
`docs/governance/DISPATCH_BASE_CONSTITUTION_v1.md`).

On this repository host these are discipline rules recorded here as much
as tooling rules: nothing but the five seed commits (S1–S5) touches `main`
directly, ever, and no lane commits directly to `main` or `integration`.

## Seed provenance

All eleven source documents `DISPATCH_MATRIX_EXECUTION_PACKAGE_v1` and
`DISPATCH_HOLD_SEED_PACKAGE_v1` assume or reference —
`DISPATCH_BUILD_BLUEPRINT_v1`, the seven pre-coding audits (architecture,
boundaries, memory, receipt workflow, Reports design, build matrix, final
review), and `DISPATCH_HOLD_IMPACT_AND_BRIEFS_v1` — were provided to this
seeding session and are copied in full under `docs/reference/`. See
`docs/reference/README.md` for the complete index.

Every contract marked `FROZEN v1.0` in `contracts/` and every adopted
section in `docs/governance/` is sourced directly from
`DISPATCH_BUILD_BLUEPRINT_v1` (field-level schemas, Part 1) or from
content the blueprint explicitly marks as an approved numbered item (see
`docs/governance/APPROVAL_REGISTER.md`). Nothing is asserted as frozen or
adopted without that sourcing.

**One deliberate exception to the blueprint's own language:** the
blueprint's Part 1.2 marks Decision D1 (dual-record fuel) "ADOPTED [MIKE
APPROVES]" and Part 1.5 marks the expense vocabulary
"[MIKE APPROVES — he may add/remove before freeze]." The blueprint's own
header defines `[MIKE APPROVES]` as "drafted for his sign-off, not yet
law." The later, dated approval record
(`DISPATCH_MATRIX_EXECUTION_PACKAGE_v1`'s approval status of 2026-08-03,
carried into `docs/decisions/DECISION_LOG.md`) lists these as items **#2**
and **#3**, both HELD. This repository follows the Decision Log, not the
blueprint's internal draft language: `fuel_record.DRAFT.json`,
`expense_record.DRAFT.json`, and `expense_vocabulary.HOLD.md` all carry
DRAFT/HELD status, not FROZEN, even though their field-level content is
fully known. The same logic applies to items **#4** (hard approval gates)
and **#14** (Trade Memory) — their draft text exists in full in
`DISPATCH_BUILD_BLUEPRINT_v1` Parts 2.1 and 2.3, but the corresponding
sections of `docs/governance/DISPATCH_BASE_CONSTITUTION_v1.md` and
`MEMORY_DOCTRINE_v1.md` stay reserved and empty, pointing at the draft
location rather than adopting it.

**Audits are advisory, not law.** The seven pre-coding audits each carry
"Authority: Advisory only. Mike Zachary is final authority" in their own
headers. Rich, well-formed recommendations in those audits (the full
Company/Trade Memory lifecycle, freeze/journeyman-exam mechanics, the
storage read/write matrix, backup doctrine) are recorded where relevant
as explicitly-labeled **recommendations awaiting adoption**, not treated
as settled contracts, even where no other information contradicts them.
Only `DISPATCH_MATRIX_EXECUTION_PACKAGE_v1`'s approval status and
`DISPATCH_BUILD_BLUEPRINT_v1`'s Part-1 contract fields carry adopted
weight.

See `docs/decisions/DECISION_LOG.md` and `contracts/CONTRACT_REGISTER.md`
for exactly what is and is not settled, item by item.

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

## Seed transparency notice — read before trusting anything under `contracts/` or `docs/governance/`

`DISPATCH_HOLD_SEED_PACKAGE_v1` assumes several source documents are
available to the seeding session: `DISPATCH_BUILD_BLUEPRINT_v1`, seven
prior audit documents (including `DISPATCH_RECEIPT_WORKFLOW_AUDIT_v1`),
`DISPATCH_HOLD_IMPACT_AND_BRIEFS_v1`, and
`DISPATCH_REPORTS_DESIGN_REVIEW_v1`.

**Only `DISPATCH_MATRIX_EXECUTION_PACKAGE_v1` and
`DISPATCH_HOLD_SEED_PACKAGE_v1` were actually provided to this seeding
session.** Those two documents describe *that* contracts and doctrine
clauses exist and are approved/held, but do not carry their full
field-level or clause-level text.

Per `CONSTITUTION.md` Rule 11 (No Fabrication — "Unknown means Unknown"),
this seed does **not** invent that missing text. Every file in
`contracts/` and `docs/governance/` that depends on content from a
document not provided says so explicitly in a `STATUS` / `status` field
instead of guessing:

- No contract in this repository is marked `FROZEN` unless its field-level
  content was actually sourced from a provided document. Marking
  fabricated content `FROZEN v1.0` would itself be a fabrication, and
  would hand later lane sessions false law to build against.
- Governance documents that the seed package expects to be fully drafted
  (e.g. `LIBRARIAN_CONSTITUTION_v1.md`) instead carry an authority block,
  the doctrine numbers known to be approved, and everything actually
  stated about them in the two provided documents — with a `PENDING
  SOURCE` marker on anything else.

This is a deliberate, flagged deviation from the seed package's literal
S2/S3 instructions. See `docs/reference/README.md` for the full list of
missing source documents, and `docs/decisions/DECISION_LOG.md` /
`contracts/CONTRACT_REGISTER.md` for exactly what is and is not settled.
**No lane session should treat a `PENDING SOURCE` file as ready to build
against — that gap must close (Mike supplies the real text) before that
lane opens for real, per the seed completion test.**

# LANE B LAUNCH PACKAGE — Manager Work Queue

Purpose: a launch-ready build packet for Lane B, current as of commit
`7f5f039` on `integration` (Lane A merged). Supersedes Packet B in
`docs/reference/DISPATCH_MATRIX_EXECUTION_PACKAGE_v1.md` for two reasons —
see §9.
Repository: `jax1313-outlook/hold`, branch `build/manager-queue`.
Authority: Mike Zachary is final authority. This document contains no
implementation code and does not itself open a build session.

---

## 1. Mission

Build the single escalation channel of Dispatch: the decision/review
queue and its human interface. Every approval, exception, and quarantine
in the system terminates here. Its constitutional behaviors — silence is
never consent, the full queue is always visible, nothing is ever silently
discarded — are features to be tested as hard as the mechanics.

## 2. Files to create

All new files. Nothing in this list exists yet (`src/dispatch/queue/**`
and `tests/lane_b/**` currently hold only `.gitkeep` placeholders).

**`src/dispatch/queue/`**
- `store.py` — queue store per `contracts/queue_item.schema.json`:
  create, read, list (full queue, always — filters are views over this,
  never a second, smaller source of truth), and the four transition
  functions (`start_review`, `approve`, `reject`, `resolve`), each one
  requiring `decided_by` and writing an audit entry via
  `dispatch.common.audit` (the real module — Lane A has merged, no stub
  needed for this one; see §9).
- `app.py` (or `__init__.py` + `app.py`, whichever keeps Flask wiring
  small) — the Flask queue UI: a priority-grouped list view, an item
  detail view (subject, payload refs, an evidence preview obtained by
  calling `dispatch.evidence.interface.EvidenceSpine.retrieve()` — the
  real interface, not a stub) and rejected/approved/resolved with a
  required `decided_by` field and an optional `decision_note`.
- `templates/`, `static/` — tablet-friendly: big touch targets, no
  crowding, per the Reports design review's UI conventions (Part 3.1's
  Flask + server-rendered HTML, no JS framework).
- `README.md` — documents the queue store's public functions and the
  transition state machine, the same way `src/dispatch/evidence/README.md`
  documents Lane A's interface (required deliverable, same pattern).

**`tests/lane_b/`** — the full Lane B test suite (§6).

**`tests/stubs/`** (optional — see §9 on why these are no longer
required, only still useful for fast isolated unit tests): `audit_stub.py`,
`evidence_stub.py`, matching the real modules' signatures, kept
deliberately dumb.

## 3. Files to modify

- `docs/lanes/B/NOTES.md` — update at the end of the session: what was
  built, what was flagged, what was deliberately not built. Currently
  reads "nothing yet."
- `requirements.txt` — add `flask` (not yet a dependency; Lane A never
  needed it). Nothing else Lane A added should need to change.

Nothing else. `contracts/**`, `docs/governance/**`,
`src/dispatch/common/**`, `src/dispatch/evidence/**` (Lane A's, read-only
to this lane), and every other lane's directory are forbidden files (§8)
— read, never write.

## 4. Dependencies

- Contracts 1.3 (`queue_item.schema.json`) and 1.6 (`audit_entry.schema.json`).
- Approved doctrines: #5 (failure doctrine), #7 (Manager boundary clause)
  — both APPROVED 2026-08-03.
- **Lane A, for real** (not a stub): `dispatch.common.audit.write_audit_entry`
  and `dispatch.common.db.bootstrap` for the audit trail;
  `dispatch.evidence.interface.EvidenceSpine.retrieve` for the item-detail
  evidence preview. Lane A merged into `integration` 2026-08-04 — Lane B
  branches from that tip (this branch already does) and imports the real
  packages directly. See §9.

## 5. Contract references

| Contract | File | Status | Relevance to Lane B |
|---|---|---|---|
| Queue Item | `contracts/queue_item.schema.json` | FROZEN v1.0 | The record this lane creates and manages end to end |
| Audit Entry | `contracts/audit_entry.schema.json` | FROZEN v1.0 | Every transition writes one, via Lane A's real audit writer |
| Evidence Record | `contracts/evidence_record.schema.json` | FROZEN v1.0 | Read-only, via `EvidenceSpine.retrieve()`, for the item-detail evidence preview |

**Not needed by Lane B:** `fuel_record.schema.json`,
`expense_record.schema.json`, `expense_vocabulary.schema.json`,
`mileage_record.schema.json` — Lane B's queue is content-agnostic; it
never inspects what a `payload_refs` entry points to beyond handing it to
Lane A's `retrieve()` for display.

## 6. Test requirements

Per `DISPATCH_BUILD_BLUEPRINT_v1` Section 5 and
`DISPATCH_MATRIX_EXECUTION_PACKAGE_v1` Packet B validation gates:

1. **Contract conformance** — every queue item this lane produces
   validates against `queue_item.schema.json`; extend the shared
   `tests/conformance/` suite from Lane A (generated once, reused by
   every lane) rather than starting a second one.
2. **Golden regression:**
   - Full lifecycle: `open → in_review → approved` and
     `open → in_review → rejected` and `open → in_review → resolved`,
     each transition writing a well-formed audit entry.
   - Decided items are retained, with their `decision_note`, permanently.
   - Priority triage groups items correctly (`urgent` / `today` /
     `whenever`) without ever inventing a label Mike didn't write.
3. **Boundary refusal (negative tests) — test as hard as the features:**
   - **No code path and no configuration flag can transition an item on
     a timer, scheduler, or default.** Don't just fail to find a
     scheduler in the code — write a test that tries to construct the
     auto-approval condition (e.g. simulate the clock advancing, a
     missing `decided_by`) and asserts it's structurally impossible, the
     same way Lane A proved immutability by grepping for forbidden SQL,
     not just by reading the code carefully.
   - **The full queue is always visible; a filtered/grouped view alters
     nothing in storage.** Prove a filtered list is a read-only
     projection: applying a filter, then reading the unfiltered store,
     returns every item that existed before the filter was applied.
   - **No delete of a queue item is impossible... i.e. delete is
     impossible.** Same pattern Lane A used: install a delete-revoking
     trigger on `queue_items` (Lane A's `db.bootstrap()` does not
     currently install one on this table — Lane B's store layer needs to
     add it, since Lane A only guaranteed it for `evidence_records`,
     `evidence_children`, and `audit_log`; see §9 and §10 risk #1) and
     verify by direct-SQL attempt *and* by grep of the module surface,
     same as Lane A's `test_no_update_delete_sql.py`.
4. **Audit completeness** — every transition in the test run produced a
   well-formed audit entry; sampled and verified.

## 7. Acceptance criteria (Definition of Done)

- All Lane B tests green, including every negative test in §6.
- Conformance suite (extended, not duplicated) green.
- Every transition writes a valid audit entry (contract 1.6 shape).
- `src/dispatch/queue/README.md` documents the store's functions and the
  transition state machine.
- `docs/lanes/B/NOTES.md` updated: built / flagged / deliberately not
  built.
- **Mike's walkthrough**, run the same way Lane A's was (per
  `docs/reference/WALKTHROUGH_PROCEDURE_v1.md`): approve one item and
  reject one item in a throwaway sandbox, watched step by step.
- **Docs match as-built:** if anything built diverges from
  `MANAGER_CONSTITUTION_v1.md` or this launch package, the divergence is
  resolved in the documents before merge.
- Branch `build/manager-queue` ready for `integration` (merges after Lane
  A — already true structurally, since this branch's history contains
  Lane A's merge).

## 8. Expected deliverables

Working `dispatch.queue` package (store + Flask UI); `README.md` for the
store's functions; Lane B tests green; updated `docs/lanes/B/NOTES.md`;
branch `build/manager-queue` ready for `integration`.

**Forbidden files** (touching these is a failed gate, even if the change
is correct): `contracts/**` (read-only) · `config/dispatch.config.json`
(production — must not exist yet) · `src/dispatch/common/**` and
`src/dispatch/evidence/**` (Lane A's real modules — import and use them,
never edit them) · `src/dispatch/{receipt,ifta,reports}/**` ·
`library_seed/Constitutions/**` · anything outside this repository.

**Must not:** bridge external systems or route data payloads (the
Manager routes decisions, never data — `DISPATCH_BOUNDARY_AUDIT_v1`
Section 1's first closed door); let silence be consent under any
circumstance (second closed door); discard filtered items (third closed
door); execute domain work, call external systems, or commission workers;
add notifications beyond the UI in v1 (flag ideas in `NOTES.md` instead);
expand scope.

## 9. What changed since Packet B was written

Packet B (`docs/reference/DISPATCH_MATRIX_EXECUTION_PACKAGE_v1.md`) was
written 2026-08-03, when #2/#3/#4/#14 were still held and Lane A had not
started. Two things are different now:

1. **All 14 approval items are APPROVED** (`docs/decisions/DECISION_LOG.md`).
   Per the same logic as Lane A's launch package §9: Lane B's own scope
   never depended on any of the four — its mechanics are gate-agnostic,
   as Packet B itself said. Nothing to re-derive here.
2. **Lane A has actually merged into `integration`** (2026-08-04, this
   branch's own history contains that merge). Packet B's build prompt
   says to depend on "vendored stub[s] with identical signature until
   Lane A merges, then swapped." That condition has already happened —
   `dispatch.common.audit` and `dispatch.evidence.interface` are real,
   tested, walked-through modules sitting in this repository right now.
   Lane B should import them directly. Building the stubs listed in §2 is
   now optional, useful only if Lane B's own session wants fast unit
   tests that don't spin up a real SQLite connection — not a hard
   dependency-ordering requirement anymore.

## 10. Risks

1. **`queue_items` has no delete-revoking trigger yet.** Lane A's
   `db.bootstrap()` (`src/dispatch/common/db.py`) only installs
   immutability triggers on `evidence_records`, `evidence_children`, and
   `audit_log` — `mileage_records` and `queue_items` were left to their
   owning lanes deliberately (Lane A's launch package scoped the trigger
   set explicitly to those three tables). "No delete of a queue item,
   ever" is Lane B's own constitutional requirement (`MANAGER_CONSTITUTION_v1`),
   not Lane A's — Lane B's store layer must add that enforcement itself,
   the same way (a `BEFORE DELETE` trigger that aborts, verified by a
   direct-SQL negative test), since `src/dispatch/common/db.py` is a
   forbidden file for this lane to edit. **Mitigation:** either extend the
   store layer to install an additional trigger on `queue_items` at
   startup (a migration-style `ALTER`/`CREATE TRIGGER IF NOT EXISTS`
   Lane B's own code runs, not a `common/db.py` edit), or flag this gap in
   `NOTES.md` if a decision is needed on where that trigger should
   actually live long-term (a legitimate open question: should
   `common/db.py` eventually own every table's immutability policy, given
   later lanes will hit the same question for `mileage_records`,
   `fuel_records`, etc.?). Don't silently skip it — "no delete, ever" is
   a named constitutional behavior, not an implementation detail.
2. **Silence-is-never-consent is an absence, which is hard to test.**
   Proving a negative ("no code path can auto-approve") is easy to get
   wrong by only checking the code you wrote, not the space of code you
   didn't. Mitigation: structure the negative test the way Lane A
   structured its no-UPDATE/DELETE-SQL test — a static grep across the
   module surface for anything resembling a scheduler, timer, or default
   transition, plus a behavioral test that leaves an item untouched for a
   simulated long time and asserts its status is still `open`.
3. **Flask UI on a tablet is easy to get subtly wrong** (small touch
   targets, dense layouts) without a device to test on. Mitigation:
   design for large touch targets deliberately (buttons, not links, for
   approve/reject/resolve; generous spacing) and have Mike's walkthrough
   explicitly include viewing it at a tablet-sized browser window, not
   just confirming the backend logic works.
4. **Evidence preview coupling.** Calling `EvidenceSpine.retrieve()` from
   the queue UI means a hash-mismatch on a referenced evidence record
   (Lane A's own quarantine path) surfaces *inside* Lane B's UI. Decide
   deliberately how that's shown (e.g. "evidence integrity check failed —
   see exception queue" rather than a raw stack trace) rather than letting
   an unhandled exception break the item-detail page.
5. **Scope creep into notifications or external routing.** Both are
   explicitly excluded from Group 1. Treat §8's "must not" list as a hard
   stop, the same way Lane A treated its own.

## 11. Rollback plan

`build/manager-queue` currently contains nothing beyond what it shares
with `integration` (Lane A's merged work) — there is no Lane B-specific
work to lose yet.

If a Lane B session needs to be abandoned or restarted:

1. Before abandoning, write whatever is known to `docs/lanes/B/NOTES.md`
   (built / flagged / deliberately not built).
2. `git reset --hard` (or re-branch) `build/manager-queue` back to
   `integration`'s current tip — this discards only Lane B's in-progress
   work; Lane A's already-merged work is untouched either way, since it's
   shared ancestor history, not something Lane B could roll back even by
   mistake.
3. Delete any sandbox directories the aborted session created on disk —
   these are outside the repository and outside version control.
4. No `integration` or `main` rollback is needed unless a Lane B merge
   *had already happened* and needed reversal — not applicable yet.

## 12. Ready-to-run build prompt

```
You are building LANE B of Dispatch Matrix Group 1 in the Hold repository,
branch build/manager-queue. You are a bounded build session.

STATUS (2026-08-04): all 14 approval items are APPROVED. Lane A (Librarian
Evidence Spine) has MERGED into integration -- this branch's own history
already contains that merge. dispatch.common.audit and
dispatch.evidence.interface are real, tested, walked-through modules.
Import and use them directly; do not build or depend on stubs for
dependency-ordering reasons (that condition no longer exists). If any
thread of work seems to need a decision that isn't in
docs/decisions/DECISION_LOG.md's Resolved section, STOP that thread and
record it in docs/lanes/B/NOTES.md -- do not assume.

READ FIRST: docs/lanes/B/LANE_B_LAUNCH_PACKAGE_v1.md in full;
docs/governance/DISPATCH_BASE_CONSTITUTION_v1.md;
docs/governance/MANAGER_CONSTITUTION_v1.md;
docs/reference/DISPATCH_BOUNDARY_AUDIT_v1.md Section 1 (the three doors);
docs/reference/DISPATCH_BUILD_BLUEPRINT_v1.md Parts 1.3, 1.6, 3, 4.2, 5;
contracts/queue_item.schema.json, audit_entry.schema.json;
src/dispatch/evidence/README.md (the interface you'll be calling into);
docs/reference/WALKTHROUGH_PROCEDURE_v1.md (how the human walkthrough
gate works for every lane from here on).

BUILD: src/dispatch/queue/ -- store per contract 1.3 (create, list-the-
full-queue, and open->in_review->approved/rejected/resolved transitions,
each requiring decided_by, each writing an audit entry via
dispatch.common.audit.write_audit_entry); priority triage
urgent/today/whenever (labels Mike writes, never invented). A
delete-revoking trigger on queue_items installed by this lane's own store
layer at startup (Lane A's common/db.py deliberately does not cover this
table -- see launch package risk #1). Flask UI: list grouped by priority;
item detail with subject, payload refs, an evidence preview via
dispatch.evidence.interface.EvidenceSpine.retrieve(); approve/reject/
resolve requiring decided_by, supporting decision_note. Big touch targets,
tablet-friendly, no crowding. Add flask to requirements.txt.

CONSTITUTIONAL BEHAVIORS -- test as hard as features:
- No transition ever fires on a timer, scheduler, or default. No code path
  and no config flag can auto-approve. Prove it with a negative test, not
  just an absence of a scheduler in the code you wrote.
- The full queue is always visible; filtered/grouped views are read-only
  projections, never a second source of truth, never a deletion.
- Rejected/resolved items are retained with their notes, permanently. No
  delete of a queue item, ever -- verified by direct-SQL attempt AND by
  grep of the module surface, same pattern as Lane A's immutability tests.

MUST NOT: edit contracts/, src/dispatch/common/, or src/dispatch/evidence/
(Lane A's -- import, never edit); bridge external systems or route data
payloads; let silence be consent under any circumstance; discard filtered
items; execute domain work or commission workers; add notifications beyond
the UI; expand scope (flag ideas in NOTES.md instead).

DONE WHEN: lifecycle, no-timer, visibility, retention/no-delete, and audit
tests green; conformance suite (extended from Lane A's, not duplicated)
green; src/dispatch/queue/README.md and docs/lanes/B/NOTES.md written;
branch ready for integration. Mike's walkthrough (approve one item, reject
one item, in a throwaway sandbox, run per
docs/reference/WALKTHROUGH_PROCEDURE_v1.md) still required before merge --
green tests alone are not sufficient.
```

---

*End of LANE_B_LAUNCH_PACKAGE_v1. Documentation only; no implementation
code; does not itself open a build session.*

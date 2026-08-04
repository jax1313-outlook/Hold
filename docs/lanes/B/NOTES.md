# Lane B — Manager Work Queue — NOTES

Branch: `build/manager-queue`. Packet: `docs/lanes/B/LANE_B_LAUNCH_PACKAGE_v1.md`.
Merges after Lane A (already true structurally: this branch's history
already contains Lane A's merge into `integration`).

Update this file at the end of every Lane B session. Do not delete prior
entries — append.

## Session 1 (2026-08-04)

### Built

- `src/dispatch/queue/store.py` — `QueueStore`: `create` (requires an
  explicit `priority`, no default), `get`, `list_all` (the full queue by
  default; `status`/`priority` are read-only filters, never a second
  source of truth), and the transition methods `start_review` /
  `approve` / `reject` / `resolve`. Installs its own no-delete trigger on
  `queue_items` at construction time (idempotent) — see "Flagged" below.
  Every transition writes an audit entry via Lane A's real
  `dispatch.common.audit.write_audit_entry`, no stub.
- `src/dispatch/queue/app.py` — Flask UI: `create_app(config)` factory;
  `/` (priority-grouped list, optional `?status=` filter), `/items/<id>`
  (detail + evidence preview via Lane A's real
  `EvidenceSpine.retrieve()`), and `POST /items/<id>/{start_review,
  approve,reject,resolve}`. Templates + `static/style.css`: big touch
  targets, generous spacing, tablet-friendly per the stack rationale.
- `src/dispatch/queue/README.md` — documents the store's functions and the
  transition state machine (same pattern as Lane A's evidence README).
- `tests/lane_b/`: full lifecycle, invalid-input rejection, visibility
  (filters never shrink the full queue), no-delete (direct-SQL + grep,
  same pattern as Lane A's immutability tests), no-timer-transition (grep
  for scheduling/auto-approval tokens + a behavioral check that a
  deliberately backdated item never transitions on its own), priority
  triage, audit completeness, and full Flask route coverage including the
  evidence-preview failure paths (unknown ref, tampered/integrity-failed
  ref). 120 tests total across the repo (Lane A + Lane B + conformance),
  all green.
- `tests/conformance/test_queue_item_lifecycle_conformance.py` — extends
  Lane A's shared conformance suite: every status the state machine can
  reach (`open`, `approved`, `rejected`, `resolved`, with `payload_refs`)
  validates against `contracts/queue_item.schema.json`.
- `requirements.txt` — added `flask`.

### Flagged (design decisions made without a live Mike decision)

1. **`queue_items`' no-delete trigger lives in `store.py`, not
   `common/db.py`.** Flagged as an open risk in
   `LANE_B_LAUNCH_PACKAGE_v1.md` §10 risk #1 before this session started.
   Resolved by having `QueueStore.__init__` call
   `install_immutability()` (an idempotent `CREATE TRIGGER IF NOT
   EXISTS`) every time a store is constructed, rather than editing Lane
   A's `common/db.py` (a forbidden file for this lane). This does mean
   the guarantee only holds once at least one `QueueStore` has been
   constructed against a given database file — acceptable for this
   lane's actual usage (the Flask app and every test construct one
   immediately), but worth surfacing if a later lane ever writes to
   `queue_items` without going through this store.
   `UPDATE` is deliberately *not* blocked on this table, unlike Lane A's
   three immutable tables — transitions require it.
2. **A real threading bug that only appeared outside the automated test
   suite.** The first implementation shared one `sqlite3.Connection`
   across every Flask request (built once in `create_app()`). All 120
   automated tests passed against this version, because Flask's test
   client runs synchronously in the calling thread. A manual smoke test
   against the *real* `python -m dispatch.queue.app` dev server hit
   `sqlite3.ProgrammingError: SQLite objects created in a thread can only
   be used in that same thread` on the very first request. Fixed by
   opening a fresh, thread-local connection per request via `flask.g`,
   closed in `teardown_appcontext`. Recorded here because it's a concrete
   example of why `docs/reference/WALKTHROUGH_PROCEDURE_v1.md` (and the
   general instruction to actually run a UI change, not just test it)
   matters — this bug was invisible to every test and would have shipped
   silently otherwise.
3. **Evidence-preview failure handling.** Per launch package risk #4: an
   unknown `payload_refs` entry renders "No evidence record found," and a
   hash-mismatched one renders "Evidence integrity check failed... see
   exception queue" — neither raises an unhandled exception on the
   item-detail page. Implemented as a best-effort per-ref preview loop in
   `app.py`, not inside the store.

None of the above required a decision on hold in
`docs/decisions/DECISION_LOG.md` — implementation choices inside Lane B's
own scope, made explicit here per "docs match as-built."

### Deliberately Not Built

Per launch package §8's "must not" list and `MANAGER_CONSTITUTION_v1`'s
three closed doors:

- No external system integrations or data-payload routing — the queue
  routes decisions, never payloads.
- No notifications beyond the UI itself (no email/SMS/webhook on new
  urgent items — flagging as a future idea, not building it now).
- No domain work execution or worker commissioning.
- `tests/stubs/audit_stub.py` / `evidence_stub.py` were not built — Lane A
  had already merged before this session started, so the
  stub-until-merge condition never applied (see launch package §9). Real
  modules are imported directly throughout.
- No production config anywhere in this repository.

### Still outstanding before this lane can merge

- ~~**Mike's sandbox walkthrough**~~ — done. See
  `docs/lanes/B/WALKTHROUGH_REPORT_v1.md`: approve one item, reject one
  item, plus a bonus check that an already-decided item refuses a second
  decision (400, no change) — run against the real Flask dev server, not
  the test client, per `docs/reference/WALKTHROUGH_PROCEDURE_v1.md`. Mike
  approved and instructed the merge; recorded in
  `docs/decisions/DECISION_LOG.md` ("Lane B merge approval — APPROVED,
  2026-08-04").

## Session 2 (2026-08-04) — merge

`build/manager-queue` merged into `integration` following Mike's
walkthrough sign-off (above).

# dispatch.queue — the Manager's work queue

Implements contract 1.3 (`contracts/queue_item.schema.json`): the single
escalation channel every approval, exception, and quarantine in the
system terminates at.

## Construction

```python
from dispatch.common.db import bootstrap
from dispatch.queue.store import QueueStore

conn = bootstrap(config["database"])
store = QueueStore(conn)
```

Same dependency-injection pattern as Lane A's `EvidenceSpine`: a
connection and (for the Flask app) a `roots` dict come from the caller, so
nothing in this module hardcodes a root or a database path.

## The state machine

```
        create()
           |
           v
         open  ------ start_review() ------>  in_review
           |                                       |
           |  approve()/reject()/resolve()         |  approve()/reject()/resolve()
           v                                       v
   approved / rejected / resolved  <---------------+
```

- `approve`, `reject`, and `resolve` are each reachable directly from
  `open` **or** from `in_review` — review isn't mandatory, it's an
  optional intermediate state for items that need more than a single
  glance.
- Once an item reaches `approved`, `rejected`, or `resolved`, there is no
  transition back to `open` or `in_review`, or between the three decided
  states. Decisions are final: "rejected/resolved items are retained with
  their notes, permanently" (`MANAGER_CONSTITUTION_v1`) means retained
  *as decided*, not reopened.
- Every transition function is a real Python method call requiring
  explicit arguments. There is no code path that reaches any of these
  functions without a caller invoking them.

## `create(*, type, source_worker, priority, subject, payload_refs=None)`

`priority` has no default. It's a triage label Mike writes
(`urgent`/`today`/`whenever`), never one the Manager invents — passing an
unrecognized or omitted priority raises `ValueError` rather than falling
back to something reasonable-looking.

## `list_all(*, status=None, priority=None)`

Returns the full queue by default. `status`/`priority` are read-only
filters over the same underlying table — they narrow what one call
returns, they never narrow what's *in* the queue. Calling this with no
arguments after any number of filtered calls always returns everything
that exists. This is the literal implementation of "the full queue is
always visible; filtered items are deferred and logged, never discarded"
(`MANAGER_CONSTITUTION_v1`) — filtering is a view, storage doesn't shrink.

## `approve` / `reject` / `resolve(queue_item_id, *, decided_by, decision_note=None)`

`decided_by` is required with no default — omitting it (or passing an
empty string) raises `ValueError` before any database write happens. This
is the concrete form of "silence is never consent": there is no way to
decide an item without a caller supplying a human identifier, and no
timer, scheduler, or default anywhere in this module that could supply
one on a caller's behalf. Each call writes exactly one audit entry.

## Immutability

`MANAGER_CONSTITUTION_v1`: "no delete of a queue item, ever." Lane A's
`dispatch.common.db.bootstrap()` only installs delete-revoking triggers on
`evidence_records`, `evidence_children`, and `audit_log` — `queue_items`
was deliberately left to whichever lane owns it. `QueueStore.__init__`
installs that trigger itself (`install_immutability()`, idempotent) the
first time a store is constructed against a given database. `UPDATE` is
**not** similarly forbidden here — transitions are legitimate updates to
`status`/`decided_by`/`decided_at`/`decision_note`, required by the state
machine above; only `DELETE` is a hard stop.

## The Flask UI (`app.py`)

`create_app(config)` returns a Flask app wired to one `QueueStore` and one
`dispatch.evidence.interface.EvidenceSpine` (the real Lane A module, not a
stub — see `docs/lanes/B/LANE_B_LAUNCH_PACKAGE_v1.md` §9).

- `GET /` — the priority-grouped list, with an optional `?status=` filter.
- `GET /items/<id>` — item detail: metadata, an evidence preview for each
  `payload_refs` entry (best-effort — an entry that isn't an evidence
  record, or one that fails its hash check, renders a plain message
  instead of raising), and a decision form.
- `POST /items/<id>/start_review`, `/approve`, `/reject`, `/resolve` — the
  only ways any item's status ever changes. `approve`/`reject`/`resolve`
  each require a non-empty `decided_by` form field; the route returns
  `400` without touching the store if it's missing.

No route, background task, or config flag in this file can transition an
item without a human submitting a form.

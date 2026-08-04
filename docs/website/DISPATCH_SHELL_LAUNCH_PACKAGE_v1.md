# DISPATCH_SHELL_LAUNCH_PACKAGE_v1

Documentation only; no implementation code. Written per the brainstorming
process (2026-08-04), following the same launch-package convention every
prior lane and the DispatchPilot phase used. Validated with Mike across
five clarifying rounds before being written: purpose, repository, merge
scope, Pilot's role, dashboard content, and visual style are all
resolved below — see docs/decisions/DECISION_LOG.md for the record of
each.

## 1. Mission

Mike's own unified front door: today he has two separate, unstyled Flask
dev-server processes (Queue on :8484, Reports on :8485) with no shared
navigation, and DispatchPilot has no web presence at all — it's a Python
function he doesn't run himself. This package builds `dispatch.shell`: a
new, thin Flask app that becomes the one URL/one port Mike actually
bookmarks. It **mounts** Queue's and Reports' existing, completely
unmodified apps at `/queue` and `/reports` (Werkzeug's
`DispatcherMiddleware` — their route definitions, templates, and static
files change not at all), and adds its own two things neither existing
app has: a home dashboard (open queue by priority, DispatchPilot's
current folder state, recent saved reports — one glance, matching every
other screen in this system's own "tablet-sized screen" ethos) and a
`/pilot` page with a real "Process Inbox" button, closing the one actual
gap DispatchPilot has — Mike needing a terminal to run it.

This is explicitly **not** a redesign, a merge, or a rewrite of Queue or
Reports. It is exactly as thin as it can be: zero new tables, zero new
contracts, zero writes of its own. Its only write action calls Pilot's
own real, already-governed `process_inbox()` — the shell owns no state.

## 2. Files to create

- `src/dispatch/shell/__init__.py`
- `src/dispatch/shell/app.py` — `create_app(config)`: builds the shell's
  own Flask app (`/`, `/pilot`, `/pilot/process` POST), then wraps it in
  `werkzeug.middleware.dispatcher.DispatcherMiddleware` mounting
  `dispatch.queue.app.create_app(config)` at `/queue` and
  `dispatch.reports.app.create_app(config)` at `/reports` — both called
  exactly as their own modules already expose them, no wrapper, no
  subclassing, no route redefinition.
- `src/dispatch/shell/templates/{base,dashboard,pilot}.html`
- `src/dispatch/shell/static/style.css` — the shell's **own** copy of
  the same minimal look Reports already has (system font, ~18px base,
  `#fafafa` background) — not imported cross-app (Flask's static
  serving is per-app-instance; a shared file would fight the mounting
  model), just visually matching, the same way Queue's and Reports'
  stylesheets already independently match each other today.
- `src/dispatch/shell/README.md`
- `tests/shell/__init__.py`, `tests/shell/conftest.py`,
  `tests/shell/test_app.py`

## 3. Files to modify

**None.** Zero diffs to `src/dispatch/queue/**` or
`src/dispatch/reports/**` is itself a Definition-of-Done item (§7),
verified with `git diff --stat` showing no lane files touched, not just
asserted.

## 4. Dependencies

- `werkzeug.middleware.dispatcher.DispatcherMiddleware` — already a
  transitive dependency via Flask; **no new entry in `requirements.txt`**.
- Real, already-governed read APIs this package calls but never
  reimplements: `dispatch.queue.store.QueueStore.list_all()` (Lane B);
  `dispatch.reports.snapshot.recent_reports()` for the dashboard's
  recent-reports list and `dispatch.reports.queries.pending_review_count()`
  if needed, both against `dispatch.reports.readonly.open_read_only()`
  (Lane D — the same read-only connection Reports itself uses); and
  `dispatch.pilot.intake.PilotIntake` (folder contents + `process_inbox()`
  for the one write action).
- `dispatch.common.db.bootstrap` for the shell's own read-write
  connection (needed only to construct a `PilotIntake`, which itself
  needs write access for its real evidence/queue writes — the shell
  itself issues no SQL of its own, ever).

## 5. Contract references

None. This package touches no FROZEN contract and defines no new schema
— it is a pure aggregation/presentation layer over reads and writes that
already exist and are already governed elsewhere.

## 6. Test requirements

- **Mounting works end to end, for real.** `GET /queue/` and `GET /reports/`
  through the shell's own test client serve Queue's and Reports' actual
  pages, unmodified — not a re-implementation, not a proxy stub. This is
  the one genuine technical risk in this package (Flask's `url_for`
  depends on `SCRIPT_NAME` being set correctly by the middleware for
  each mounted app) — verify BOTH with an automated test and a live
  manual smoke test against the real running server, the same standard
  every prior lane used, precisely because "the theory says this should
  work" isn't the same as "it does."
- **Dashboard reflects real state.** Seed real queue items (varying
  priority), real DispatchPilot folder contents, and a real saved
  report; confirm the dashboard's counts/summaries match — not a
  hand-typed fixture pretending to be these things.
- **Process Inbox button, real end to end.** A `POST /pilot/process`
  against a real seeded Inbox produces the same outcome
  `dispatch.pilot.intake.process_inbox()` would if called directly —
  same routing, same evidence registration, same audit trail — proving
  the button doesn't reimplement or diverge from the real pipeline.
- **No new write path.** A grep test (same technique as Lane D's
  no-tax-math/no-DELETE guards): `src/dispatch/shell/**` never issues a
  raw SQL `INSERT`/`UPDATE`/`DELETE` anywhere — every write happens by
  calling another lane's real, already-tested write API.
- **Zero lane diffs.** A test (or a build-step check) confirming
  `src/dispatch/queue/**` and `src/dispatch/reports/**` are byte-identical
  to `integration`'s current tip after this package is built.
- **Failure handling.** If `process_inbox()` raises (e.g. a genuinely
  malformed file it can't even register), the `/pilot` page shows a
  clear message, not a raw 500 — matching Reports' own "no report
  renders without complete data" instinct applied to a write action
  instead of a query.

## 7. Acceptance criteria (Definition of Done)

- One port, one URL, three real screens: `/` (dashboard), `/queue`
  (Lane B, unmodified), `/reports` (Lane D, unmodified), `/pilot`
  (new).
- Dashboard shows real open-queue-by-priority counts, real DispatchPilot
  folder state, and real recent saved reports.
- "Process Inbox" button works against a real Inbox, with a real,
  visible outcome (not just a redirect with no feedback).
- All test requirements in §6 green, including the live manual smoke
  test against the real mounted server.
- `src/dispatch/shell/README.md` written.
- `docs/website/NOTES.md` written (Built / Flagged / Deliberately Not
  Built, same convention as every prior phase).
- Full repo test suite green.
- Branch ready for `integration`; Mike's walkthrough (same standing
  procedure, `docs/reference/WALKTHROUGH_PROCEDURE_v1.md`) and explicit
  sign-off still required before merge — no different from any prior
  lane.

## 8. Expected deliverables

Working `dispatch.shell` package (mounted dashboard + pilot trigger over
Queue and Reports, both byte-for-byte unmodified); `tests/shell/` green;
`src/dispatch/shell/README.md`; `docs/website/NOTES.md`; branch ready for
`integration`.

**Forbidden:** editing anything under `src/dispatch/{queue,reports}/**`
(import their `create_app`/query functions freely — never modify their
files); any new database table or contract; any write path that isn't a
call into another lane's existing real write API; authentication,
HTTPS, reverse proxies, or any other production-hardening concern
(explicitly out of scope per the standing direction); a public-facing or
customer-facing surface of any kind (this is Mike's own internal tool
only, per §1's resolved purpose).

## 9. Risks

1. **`url_for`/`SCRIPT_NAME` under `DispatcherMiddleware`.** Werkzeug
   sets `SCRIPT_NAME` per mounted app, and Flask's `url_for` is
   documented to respect it — but this is exactly the kind of
   "should work per the docs" claim this whole project has learned not
   to trust without a live check (Lane B's threading bug and Lane D's
   two lazy-schema bugs were all caught by manual smoke tests, not
   automated suites alone, exactly because the automated suite can't
   always exercise the real request path a browser would). Mitigation:
   §6 requires both an automated test and a real running-server smoke
   test specifically exercising links *generated by* Queue's and
   Reports' own templates while mounted, not just the routes directly.
2. **Static file paths under a mount prefix.** Queue's and Reports' own
   `<link rel="stylesheet" href="{{ url_for('static', ...) }}">` tags
   need to resolve correctly to `/queue/static/...` and
   `/reports/static/...` once mounted — same class of risk as #1, same
   mitigation.
3. **A large Inbox making `POST /pilot/process` slow enough to time out
   a browser request.** Not a concern at pilot scale (single-digit
   files per run, per `docs/pilot/DISPATCH_PILOT_RUN_1_REPORT_v1.md`) —
   flagged, not solved, and not a blocker for this package. If it
   becomes real, the fix is a background-job pattern, explicitly
   deferred rather than built preemptively (YAGNI).

## 10. Rollback plan

Trivial — `dispatch.shell` is new, independent, and additive. Not
running it (or deleting the package entirely) has zero effect on Queue,
Reports, Pilot, or any governed data; nothing else in the system imports
from it.

---

*End of DISPATCH_SHELL_LAUNCH_PACKAGE_v1. Documentation only; no
implementation code; does not itself open a build session.*

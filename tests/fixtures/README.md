# Lane D fixtures

Per `LANE_D_LAUNCH_PACKAGE_v1.md` §9: Lane C had not been built yet when
Packet D was originally scoped, so its fixture requirement was
necessarily hand-typed rows conforming to the frozen schema shapes, with
a *deferred* fidelity gate to re-run against real Lane C output later.

Lane C is real and merged into `integration` now. This lane's tests build
their fixture data by actually running **Lane A's `EvidenceSpine.register()`
and Lane C's `Router.route_line()`** against a throwaway sandbox — see
`tests/lane_d/conftest.py`'s `seeded_pipeline_data` fixture — rather than
hand-typing SQL rows that merely *look like* the schema. That produces
`fuel_records`/`expense_records` with genuine referential integrity
(real evidence links, real dedup keys, real routing) instead of an
approximation of it.

This substantially de-risks `REPORTS_CHARTER_v1.md`'s deferred gate
("final report fidelity... re-run against real Lane C output on
`integration` before merge 5") but does not replace it — that gate stays
explicitly open in `docs/lanes/D/NOTES.md`, per the charter's own "never
silently skipped" instruction, because this session's sandbox data, while
produced by real code, is still synthetic in content (not Mike's actual
receipts).

## The D1 cross-link note (historical, now moot)

Packet D's original build prompt warned fuel fixtures must not
"presuppose or exclude the D1 cross-link" because Decision D1 (dual-record
fuel) was undecided at the time. D1 is approved; `expense_record_id` is a
required, frozen field on `FuelRecord`. Every fuel fixture this lane uses
carries it naturally, because it's produced by the real router, which has
never had a code path that omits it.

## `ifta_worksheets` fixture data

The IFTA Position report's fixtures are built by running Lane C's real
`WorksheetEngine`/`exceptions`/`package` modules against fixture mileage
and rate data (the same `fixture-v1`-tagged rates Lane C's own tests use
— see `library_seed/RateTables/README.md`), not by hand-inserting
`ifta_worksheets` rows either.

# DISPATCH PILOT — RUN 1 REPORT

Purpose: the smallest practical operational test, run per direction —
validate Receipt Intake, Evidence Registration, Fuel Extraction, Expense
Extraction, IFTA Workflow, Queue Operations, and Reports end to end, using
realistic (synthetic) documents, and surface real operational issues.
This is **not** a certification exercise; per direction, bugs found here
are expected and useful, not failures. Run against `integration` @
`c0c89b6`, in this environment (as agreed for the first pass).

## Sandbox

`/home/user/dispatch_pilot_run1/` — a real, standalone sandbox, **kept**
(not torn down) since this run is itself the deliverable, not a
disposable build-session check. `tools/init_roots.py`,
`tools/seed_library.py`, and `tools/init_pilot.py` built the standard
skeleton plus the `DispatchPilot` tree.

## The scenario

One truck (T-104), one driver (J. Smith), a pilot week (2026-07-06 to
2026-07-10) across TX and MO, dropped into `DispatchPilot\Inbox` as nine
separate files — the way documents would actually arrive over a real
week, not one big batch:

| File | Real content |
|---|---|
| `fuel_TX_mon.csv`, `fuel_TX_wed.csv` | Two clean TX diesel fuel-card purchases |
| `fuel_MO_fri.csv` | One clean MO diesel fuel-card purchase |
| `receipts_week.csv` | A meal + a parts/maintenance expense |
| `bad_export.csv` | A fuel purchase with a wrong declared total — a real, honest mistake |
| `RateCon_XYZ_Load77.pdf` | A rate confirmation |
| `POD_Load77_signed.jpg` | A proof of delivery |
| `eld_hos_week28.csv` | An ELD hours-of-service export (different columns from a receipt CSV entirely) |
| `dispatcher_notes.txt` | A personal reminder, not a business document |

## Results by validation target

**1. Receipt Intake / Evidence Registration.** All nine files processed
in one `process_inbox()` call. Every one classified correctly on the
first real run: three fuel CSVs and one expense CSV routed through Lane
C's real, unmodified intake pipeline; the malformed CSV correctly
quarantined its one bad line (sum mismatch) without crashing; the
RateCon, POD, ELD export, and notes file all registered as real governed
evidence (real SHA-256 hashes, confirmed independently in
`evidence_records`) and landed in their matching folders.

**2. Fuel Extraction.** Three real `FuelRecord`s created — $438.90/102gal
(TX), $401.25/93gal (TX), $354.80/85gal (MO) — independently confirmed
against the CSV inputs.

**3. Expense Extraction.** Real `ExpenseRecord`s for the meal ($21.40)
and parts/maintenance ($289.50) lines, plus the dual-record fuel-linked
expense rows.

**4. IFTA Workflow.** Real mileage entered via `tools/mileage_worksheet.py`
(TX 640mi, MO 210mi), a real draft worksheet built via `WorksheetEngine`,
all ten exception detectors run for real, submit-for-approval → approve
→ seal exercised end to end — including confirming `attempt_seal`
**correctly refuses** to seal before approval exists. The sealed bundle
was independently confirmed on disk at
`Archive\IFTA\2026-Q3\<worksheet_id>.json`.

**5. Queue Operations.** Full queue read directly from storage after
everything: **7 items, all visible, none hidden** — 4 "awaiting future
processing" (whenever/review), 1 quarantined line (today/exception), 1
IFTA exception (today/exception), 1 IFTA approval (approved). One item
(the notes file) was actually resolved by "human:mike" with a real
decision note, proving the full lifecycle, not just creation.

**6. Reports.** Fuel Spend, Expense Summary, and IFTA Position all run
against the real Flask dev server, showing byte-exact matches to
independently-computed totals: Fuel Spend $1,194.95 / 280.0gal (TX
$840.15/195gal, MO $354.80/85gal); Expense Summary $1,505.85 across
`fuel`/`meals`/`parts_maintenance`; IFTA Position $0.16 net tax, 1
exception, matching the sealed worksheet exactly. Save For Printing
round-tripped cleanly. Zero errors in the Reports server log.

**7. Audit trail.** 32 real entries, one per real operation
(`librarian`, `manager`, `receipt`, `pilot`, `reports` actors), nothing
missing.

## Operational issues discovered

This is the actual point of the exercise — two real findings, neither a
crash or data-safety bug, both genuinely useful:

1. **The pilot's keyword pre-classification measurably improves operator
   trust, even though the underlying system was already safe.** Tested
   directly: if `eld_hos_week28.csv` had *not* been keyword-classified
   first, Lane C's real CSV parser would still refuse it safely (a caught
   `ValueError`, no crash, no fabricated data) — but the quarantine
   message would read "row missing required field(s): [vendor_name,
   purchase_date, ...]," which doesn't tell Mike *why* — it reads like his
   fuel-card export is broken, not like the system correctly recognized
   an unrelated document type. The pilot's classification turns that into
   a clear "New eld export awaiting future processing" instead. Worth
   remembering as this pilot's document-type coverage grows: a document
   type with no keyword match still fails *safely*, just not *legibly*.
2. **Manually-entered mileage is a real, easy-to-get-wrong dependency for
   IFTA, and the exception detector is what catches it.** The mileage
   entered for this run (640/210mi) was too low relative to the fuel
   actually purchased, producing an implausible fleet MPG (3.04) —
   `fleet_mpg_out_of_band` caught it correctly, exactly as designed, and
   the approval step required a human decision note before sealing
   anyway. But this makes concrete a real operational risk for the actual
   pilot with Mike's real mileage: manual mileage entry is the one input
   in this whole chain with no independent cross-check (fuel purchases
   are receipt-backed; mileage today is just typed in). Worth watching
   during real pilot use — if this keeps happening, it's a candidate for
   "Adjust Blueprint," not something to patch quietly here.

No crashes, no silent failures, no fabricated data, no lost documents —
every one of the nine inputs is traceable to exactly one real, correct
outcome.

## What this report is not

Same as every walkthrough before it: this documents that the exercise
ran and what it found. It is not itself an approval of anything, and (per
direction) it is explicitly not a certification that Dispatch is
"production ready" — the objective was operational learning, and this
sandbox is left intact specifically so the two findings above (and the
underlying data) can be inspected directly, not just taken on faith from
this write-up.

---

*End of DISPATCH PILOT — RUN 1 REPORT.*

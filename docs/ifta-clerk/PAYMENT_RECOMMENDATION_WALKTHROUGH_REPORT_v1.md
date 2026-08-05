# PAYMENT RECOMMENDATION WALKTHROUGH REPORT v1

Purpose: the written record of the human walkthrough required before
merge, run per the standing procedure at
`docs/reference/WALKTHROUGH_PROCEDURE_v1.md`. Repository:
`jax1313-outlook/hold`, branch `build/ifta-clerk-payment-recommendation`,
commit `0ac6e9f`.

## How this walkthrough was run

Same procedure as every prior lane and phase: Mike does not have a
terminal into this remote environment, so the build session executed
every command and showed the real, unedited output at each step. The
real interface under test was the real running mounted server
(`python -m dispatch.shell.app`) — every request below is a real HTTP
call, not the pytest test client. Real data entered through the actual
CSV receipt-intake pipeline, the actual `tools/mileage_worksheet.py`
CLI, and the actual `rates.insert_rate()`. The failure path was covered
first, before any worksheet existed at all, then again after a real
worksheet was built, submitted, approved, and sealed.

## Sandbox used

A throwaway sandbox outside the git repository:
`/home/user/ifta_payment_walkthrough/` (deleted after this walkthrough
completed), built with `tools/init_roots.py`.

## Step 1 — Recommend before any worksheet exists

```
POST /ifta-clerk/recommend-payment (quarter=2026-Q3, fuel_type=diesel) -> 400
"Could not generate payment recommendation: no worksheet has been built for 2026-Q3/diesel yet"
```

Clean, typed error, no crash. Confirmed via the filesystem that
`Archive/IFTA/` contained nothing at all — the refusal wrote no file.

## Step 2 — Real data through real entry points, two jurisdictions

A real fuel CSV (Pilot Travel Center, TX, 2026-07-20, diesel, 100.0
gallons) through the real `IntakePipeline.process_drop()` — routed
cleanly. Two real mileage entries via `tools/mileage_worksheet.py`: 800
miles in TX, 200 miles in OK. Two real rates
(`rates.insert_rate()`): TX 0.25/gal, OK 0.18/gal — chosen deliberately
to span jurisdictions with fuel purchased in only one of them, so the
resulting `total_net_tax` would be a real, non-trivial number rather
than an artificial zero.

## Step 3 — Prepare, submit, approve, seal — the full real pipeline

```
POST /ifta-clerk/prepare -> 302, .../?...&prepared=1&exceptions=2
```

Two real detector findings surfaced honestly, not suppressed:
`fleet_mpg_out_of_band` (10.0 mpg outside the plausible `[4.0, 9.5]`
band — a true consequence of the deliberately chosen mileage numbers)
and `miles_no_fuel_gap` (200.0 miles recorded in OK with 0 gallons
purchased there). Neither blocks preparation or submission — they are
informational Category 1 exceptions, exactly as designed.

```
POST /ifta-clerk/submit -> 302, .../?...&submitted=1
```

Approval and sealing are unreachable from `ifta_clerk` by design
(verified structurally in the prior branch and again here via
`ast`-parsed imports), so both were performed directly against the
real `QueueStore.approve()` and `dispatch.ifta.package.attempt_seal()`
— the same functions the real Queue app itself calls, not a shortcut:

```
sealed: {
  "ifta_worksheet_id": "01KZ7RQTNK7NJ3YG45K2HT9P7D",
  "quarter": "2026-Q3", "fuel_type": "diesel",
  "fleet_mpg": 10.0, "status": "sealed",
  "total_net_tax": -1.4000000000000004,
  "sealed_at": "2026-08-05T01:31:55Z", ...
}
```

## Step 4 — Generate the payment recommendation, for real

```
POST /ifta-clerk/recommend-payment -> 302, .../?...&recommended=1
```

Independently confirmed via the filesystem — not the app's own
claim — that exactly one new file was written:

```
Archive/IFTA/2026-Q3/01KZ7RQTNK7NJ3YG45K2HT9P7D_payment_recommendation.json
{
  "amount": 1.4000000000000004,
  "recommendation": "credit",
  "total_net_tax": -1.4000000000000004,
  "ifta_worksheet_id": "01KZ7RQTNK7NJ3YG45K2HT9P7D",
  "quarter": "2026-Q3", "fuel_type": "diesel",
  "sealed_at": "2026-08-05T01:31:55Z",
  "generated_at": "2026-08-05T01:31:58Z", "status": "recommendation"
}
```

Hand-verified: `total_net_tax = -1.4000000000000004` is negative, so
the `credit` branch applies and `amount` must equal
`abs(total_net_tax) = 1.4000000000000004` — matches exactly. The
dashboard rendered the same values: badge "RECOMMENDATION — NOT A
PAYMENT," "Net credit position: 1.40. No payment due."

## Step 5 — Idempotency, confirmed live

A second, immediate `POST /ifta-clerk/recommend-payment` also returned
302. Confirmed via the filesystem: still exactly one
`*_payment_recommendation.json` file, byte-for-byte identical,
`generated_at` unchanged (`2026-08-05T01:31:58Z` both times) — not
regenerated.

## Step 6 — Independent confirmation through a completely separate, unmodified app

```
GET /queue/ -> "Approve IFTA worksheet 2026-Q3 (diesel): net tax -1.40" · approval · approved
```

The real Queue app — never touched by this branch — independently
shows the same approved item with the same net tax figure this
workflow produced, proving the integration is real end to end.

## Definition of Done — status against the approved design

| Requirement | Status |
|---|---|
| Applies only to a sealed worksheet, refuses otherwise | Done — Step 1 |
| Wraps the sealed `total_net_tax`, invents nothing | Done — Step 4, hand-verified |
| Exactly one JSON file to Archive, no new table | Done — Step 4, filesystem-confirmed |
| No database write capability at all | Done (prior session, `read_only_conn`-only, `ast`-verified) |
| Idempotent — never regenerates | Done — Step 5 |
| Clean failure handling, not a raw crash | Done — Step 1 |
| No payment API / bank / accounting write anywhere | Done (prior session, `ast`-verified; nothing to exercise live since it doesn't exist) |
| Real integration with the existing Queue | Done — Step 6 |
| Automated tests, full suite green | Done (prior session) — 452/452, plus this independent live walkthrough |
| `docs/ifta-clerk/PAYMENT_RECOMMENDATION_NOTES_v1.md` written | Done (prior session) |
| **Mike's walkthrough** | **Done — this document** |
| Branch `build/ifta-clerk-payment-recommendation` ready for `integration` | Technically ready; final call below |

## What this report is not

Per Hard Approval Gate #7: this is evidence for a decision, not the
decision itself. Merging `build/ifta-clerk-payment-recommendation` into
`integration` still requires Mike's own affirmative approval, stated in
writing, before it happens.

---

*End of PAYMENT RECOMMENDATION WALKTHROUGH REPORT v1.*

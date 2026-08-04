# LANE A WALKTHROUGH REPORT v1 — Librarian Evidence Spine

Purpose: the written record of the human walkthrough required by
`LANE_A_LAUNCH_PACKAGE_v1.md` §7 ("Mike's walkthrough: register a real
document in sandbox, retrieve it, verify the hash. No merge on green
checks alone.") and `DISPATCH_BUILD_BLUEPRINT_v1` Part 5, gate 5.
Repository: `jax1313-outlook/hold`, branch `build/librarian-spine`, commit
`fb639e9`.

## How this walkthrough was run

Mike does not have a terminal into the remote environment this repository
and its sandbox run in — his own machine (Windows) has no connection to
it. By his explicit choice, each command below was executed by the build
session on his behalf, with the full command and its real, unedited
output shown to him at every step before proceeding to the next. This is
recorded here plainly because it is a deviation from "Mike types the
commands himself," and per `README.md`'s binding rules, divergences get
written down, not glossed over.

## Sandbox used

A throwaway sandbox, entirely outside the git repository and unrelated to
any production path: `/home/user/mike_walkthrough/`, built from
`walkthrough.config.json` (`environment: "sandbox"`, all three roots under
that one folder). `tools/init_roots.py` built the standard
OPERATIONS/LIBRARY/ARCHIVE skeleton inside it from that config — the same
tool and code path Lane A ships.

## Step 1 — Register a real document

A document (`sample_receipt.txt`, a stand-in pump receipt — Mike opted
for a stand-in over transferring a real file from his Windows machine,
since this step only exercises archiving/hashing, not receipt content)
was registered via `EvidenceSpine.register()`:

| Field | Value |
|---|---|
| `evidence_record_id` | `01KZ6DNBNQ7M438WYC6Z940PD3` |
| `archive_path` | `Evidence/2026/08/01KZ6DNBNQ7M438WYC6Z940PD3.txt` |
| `file_hash` | `6be9b10267e11c1183673dcb47798c63108d4cbd801bde1eadb0663011e7b227` |
| `extraction_status` | `complete` |
| `retention_class` | `ifta_4yr` (defaulted) |

Independently confirmed outside the application code:
- `sha256sum` on the original file matched `file_hash` exactly.
- `ls -la` on the archived copy showed `-r--r--r--` — read-only, verified
  by inspecting the actual mode bits, not assumed.

## Step 2 — Retrieve it and verify the hash

`EvidenceSpine.retrieve()` was called for the same `evidence_record_id`.
It returned the record and the archived file's path after re-verifying
the hash internally. A second, independent hash was then computed by hand
(`hashlib.sha256`, outside the retrieve() call) on the returned path:

```
Stored fingerprint:     6be9b10267e11c1183673dcb47798c63108d4cbd801bde1eadb0663011e7b227
Recomputed fingerprint: 6be9b10267e11c1183673dcb47798c63108d4cbd801bde1eadb0663011e7b227
MATCH: True
```

## Step 3 — Tamper-detection check (optional, Mike requested it)

A second document was registered (`01KZ6DSDKYMKH8EAYFG1VD73KS`), then its
archived copy was deliberately corrupted on disk (bypassing the read-only
attribute directly, as a worst-case bit-rot or attacker scenario would),
and `retrieve()` was called again:

- `retrieve()` raised `EvidenceIntegrityError` and did **not** return the
  corrupted content.
- A `queue_item` (`type: exception`, `priority: urgent`, `status: open`)
  was written referencing the record, so a human has something to act on.
- An `audit_log` entry was written with `outcome: quarantined`.

This is the Failure Doctrine (stop, quarantine, escalate) observed firing
for real, not just asserted in a test.

## Definition of Done — status against LANE_A_LAUNCH_PACKAGE_v1 §7

| Requirement | Status |
|---|---|
| All Lane A tests green, including every negative test in §6 | Done (73/73, prior session) |
| Conformance suite green | Done (prior session) |
| Every operation writes a valid audit entry | Done — reconfirmed live in this walkthrough |
| `src/dispatch/evidence/README.md` documents the three calls | Done (prior session) |
| `docs/lanes/A/NOTES.md` updated: built / flagged / deliberately not built | Done (prior session) |
| **Mike's walkthrough**: register, retrieve, verify hash | **Done — this document** |
| Docs match as-built | Done — nothing observed in this walkthrough contradicts `LIBRARIAN_CONSTITUTION_v1.md`, the launch package, or the design decisions already recorded in `NOTES.md` |
| Branch `build/librarian-spine` ready for `integration` | Technically ready; final call below |

## What this report is not

Per Hard Approval Gate #7 (`DISPATCH_BASE_CONSTITUTION_v1`): *"Approval is
an affirmative act recorded in the decision queue. Silence, timeout, or
absence is never consent."* This report records that the walkthrough
happened and what it showed. It is **not** itself Mike's sign-off, and no
build session can supply that on his behalf. Merging `build/librarian-spine`
into `integration` still requires Mike's own affirmative approval, stated
in writing, before it happens — this document is the evidence he'd be
approving against, not a substitute for the approval itself.

## Sign-off

Mike approved this walkthrough and instructed the merge into `integration`
in the same message ("yes go ahead and also merge"), 2026-08-04. Recorded
per Hard Approval Gate #7 in `docs/decisions/DECISION_LOG.md` ("Lane A
merge approval — APPROVED, 2026-08-04"). The merge was performed
immediately after in this same session.

Mike also instructed that all future lane walkthroughs (B, C, D) follow
this same procedure. That standing procedure is now written down at
`docs/reference/WALKTHROUGH_PROCEDURE_v1.md` so later, independent build
sessions don't have to re-derive it.

---

*End of LANE A WALKTHROUGH REPORT v1.*

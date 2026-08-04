# WALKTHROUGH_PROCEDURE_v1

Purpose: the standard procedure for every lane's "Mike's walkthrough" gate
(`DISPATCH_BUILD_BLUEPRINT_v1` Part 5, gate 5 — "Mike runs the lane
end-to-end on real documents in the sandbox and signs off in writing. No
merge on green checks alone."). Adopted 2026-08-04 after Lane A's
walkthrough, by Mike's instruction to run every future lane's walkthrough
"the same manner as this one." Applies to Lanes B, C, and D as each
reaches its own walkthrough gate.

Authority: Mike Zachary is final authority. This document describes
procedure, not law — it doesn't create, weaken, or substitute for any gate
in `DISPATCH_BASE_CONSTITUTION_v1` or a worker constitution.

## The procedure

1. **Throwaway sandbox, outside the repository.** Build a fresh config
   pointing all roots at a folder that isn't under version control and
   isn't a production path (e.g. `/home/user/<lane>_walkthrough/`), then
   run the lane's own `init_roots`-equivalent tool against it. Never reuse
   a prior walkthrough's sandbox folder without saying so.
2. **The build session executes; Mike watches.** Mike does not have a
   terminal into the remote environment this repository's sandbox runs in.
   By his standing instruction, the build session runs each command on his
   behalf and shows him the real, unedited command and output at every
   step — one step at a time, waiting for his acknowledgment before
   continuing. This is a documented deviation from "Mike types the
   commands himself," carried forward from Lane A's walkthrough, not a
   new decision each lane has to re-litigate.
3. **Use the lane's real interface, not a shortcut.** Every action in the
   walkthrough calls the lane's actual shipped code (e.g.
   `EvidenceSpine.register()`), never a special "demo mode." Independently
   re-verify at least one claim outside that code wherever practical (Lane
   A: recomputing a SHA-256 by hand rather than trusting the one number the
   code prints).
4. **Cover the failure path, not just the happy path.** Where the lane has
   a designed failure/quarantine behavior (Lane A: hash-mismatch-on-
   retrieve), demonstrate it firing for real inside the walkthrough sandbox,
   not only in the automated test suite.
5. **Write it down before asking for sign-off.** Produce a
   `docs/lanes/<X>/WALKTHROUGH_REPORT_v1.md`: what sandbox was used, each
   step with its real output, which values were independently
   cross-checked and how, and a table against that lane's Definition of
   Done. State plainly, in the report, that the report itself is not
   Mike's approval (Hard Approval Gate #7: approval is an affirmative act,
   never silence or a document written on someone's behalf).
6. **Wait for the affirmative act.** Only after Mike states his approval in
   his own words does the merge into `integration` happen. When he approves
   and asks for the merge in the same message (as with Lane A), record that
   approval in `docs/decisions/DECISION_LOG.md` before performing the
   merge, then merge and push in the same session.

## Why this is written down here rather than repeated per lane

`README.md`'s Hold Re-Entry Protocol note applies: "no open session ever
absorbs a decision mid-build — sessions end, follow-on packets begin."
Lane B, C, and D's build sessions will be separate sessions with no memory
of this conversation. Without this document, each would have to
re-negotiate the same procedural question ("how does a non-developer human
without direct terminal access actually perform a walkthrough?") from
scratch. This document means they don't have to.

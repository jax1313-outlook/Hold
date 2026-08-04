# DISPATCH_HOLD_IMPACT_AND_BRIEFS_v1

Purpose: map the approval decisions of 2026-08-03 onto the build plan, and give Mike a decision brief for each of the four held items.
Status basis: 10 items APPROVED (#1, #5–#13), 4 items HELD (#2, #3, #4, #14).
Authority: Mike Zachary is final authority. Nothing below proceeds past a hold.

## 1. WHAT THE TEN APPROVALS UNBLOCK

The approved set — storage mapping, failure doctrine, deletion/retention, and all seven worker boundary clauses — plus the Contract Pack items that carried no approval flag (queue item contract 1.3, archive/evidence interface 1.4, audit entry format 1.6, and the structural parts of the schemas) resolve to this lane status:

| Lane | Status | Detail |
|---|---|---|
| **A — Evidence Spine** | **FULLY UNBLOCKED — can start today** | Depends on mapping (#1 ✅), deletion doctrine (#6 ✅), failure doctrine (#5 ✅), Librarian clause (#10 ✅), and contracts 1.4/1.6 (not held). Nothing in Lane A touches a held item. |
| **B — Manager Queue** | **FULLY UNBLOCKED — can start today** | Depends on Manager clause (#7 ✅), failure doctrine (#5 ✅), queue contract 1.3 (not held). Note: the no-timer/no-auto-approve rule lives in contract 1.3 and the Manager clause, both approved — the queue's constitutional behavior is fully specified even while #4 is on hold. |
| **C — Receipt → IFTA** | **PARTIALLY BLOCKED** | Intake watcher, evidence registration, parsers, sum validation, dedup, quarantine flow, mileage worksheet, IFTA worksheet engine and exceptions: buildable now. BLOCKED: the router and the final FuelRecord/ExpenseRecord schema freeze (await #2), category validation (awaits #3), the Trade Memory component (awaits #14 — build with it disabled). |
| **D — Reports** | **MOSTLY UNBLOCKED** | Template engine, UI shell, Fuel Spend, IFTA Position, print/snapshot flow: buildable on fixtures now. Expense Summary awaits #3 (its category filter and fixtures need the frozen vocabulary). |

Practical sequencing consequence: **the holds cost nothing for roughly the first build phase.** Lanes A and B are the first two merges anyway, and Lane C's pre-router work is substantial. The holds start costing schedule the day Lane C reaches its router — so that is the natural deadline for decisions #2 and #3.

## 2. DECISION BRIEFS FOR THE FOUR HELD ITEMS

### BRIEF #2 — Dual-Record Fuel Doctrine

**The question:** when the Receipt Agent reads a diesel line, does it create one record or two?

**Why it matters:** diesel is simultaneously the IFTA tax input and the largest expense on the P&L. Whatever is decided, both the quarterly return and the books must end up complete, and they must reconcile.

**Option A — dual-record (blueprint recommendation).** Diesel emits a FuelRecord (→ IFTA) and an ExpenseRecord, category `fuel` (→ Accounting Queue), cross-linked, one Evidence parent. *For:* both consumers are complete on their own; reconciliation is a simple join on the cross-link; each agent reads only its own record type — cleanest boundaries. *Against:* two records per fuel line; the cross-link must be maintained (one more thing conformance tests verify).

**Option B — single FuelRecord; Accounting derives fuel expense from FuelRecords at posting time.** *For:* fewer records. *Against:* the Accounting Queue must now consume two record types with different shapes, the future Accounting Agent inherits a special case forever, and a FuelRecord quarantined for an IFTA issue silently goes missing from the books too — a coupling failure the audits spent three rounds preventing.

**Option C — single ExpenseRecord; IFTA reads expenses where category = fuel.** *Against, decisively:* the IFTA Agent would consume a record type not designed for it (no jurisdiction, no gallons-normalized guarantees), which reopens the round-1 defect. Not recommended under any weighting.

**Recommendation stands: Option A.** **Blocks while held:** FuelRecord/ExpenseRecord freeze, Lane C router, conformance suite for those schemas. **Decision deadline:** before Lane C's router work begins.

### BRIEF #3 — Closed Expense Vocabulary

**The question:** which categories exist? (The *principle* that the list is closed and Mike-owned was effectively approved in the Receipt boundary clause #12 — this hold is about the list's contents.)

**How to decide, three tests for each candidate category:** (1) Would you want QuickBooks or a report to slice on it? If not, it folds into a broader one. (2) Will a receipt line land in it at least monthly? If not, `misc` covers it. (3) Can a clerk assign it without judgment? If assigning it requires knowing *why* something was bought, it is too clever for extraction — keep the category physical, not intentional.

**Cost asymmetry worth knowing:** *adding* a category later is a cheap version bump — old records stay valid. *Renaming, merging, or splitting* categories later is expensive — historical records need remapping and reports cross a definition boundary. So when in doubt, leave it out; `misc` plus the review queue is the escape valve, and a `misc` item that recurs is the evidence a new category has earned its place.

**Implementation note that lowers the stakes:** the vocabulary will load from a versioned file in the Library, not from code. Freezing the list is a data decision; changing it later never requires a code change.

**Blocks while held:** ExpenseRecord category validation (Lane C router), Expense Summary report and its fixtures (Lane D). **Decision deadline:** same as #2 — Lane C router start.

### BRIEF #4 — Hard Approval Gates

**The question:** adopt the seven Base-level gates as drafted, or amend first?

**What each gate protects, in one line each:** (1) government filings — the state can't receive anything you didn't sign; (2) accounting writes — the books can't change without you; (3) binding communications — no worker can commit your money, truck, or signature (informational traffic flows freely); (4) truth demotion — the Library can't be quietly rewritten; (5) constitution amendments — only you legislate; (6) worker commissioning — only you hire; (7) silence ≠ consent — a stalled queue can never become an approval.

**The property worth weighing while reviewing:** gates are a ratchet that only works in one direction. A gate adopted strict can be *deliberately loosened later* through gate 5's own amendment process, with a version bump and full audit trail. But a gate adopted loose cannot retroactively protect anything that already happened. Starting strict costs a few taps in the queue UI; starting loose costs whatever the first ungated mistake costs.

**If the hold is about a specific gate** (most likely #3, if future auto-booking of loads is on your mind): the draft already splits informational from binding traffic, and auto-booking can be enabled later per-workflow by amendment — the gate as written doesn't foreclose it, it just makes enabling it an explicit decision instead of a drift.

**Blocks while held:** adoption of the Base Constitution amendment — a document milestone. **Does NOT block:** Lanes A, B, or D code, or Lane C's buildable scope (the queue's approval mechanics come from approved contract 1.3). **Decision deadline:** before the first merge into `integration` (gate 6 of the validation gates requires docs-match-as-built, and the Base Constitution is the root document).

### BRIEF #14 — Trade Memory Doctrine

**The question:** adopt the learning rules (closed entry types, inspection, freeze-snapshot, promotion path) as drafted?

**The option the blueprint quietly gives you — v1 can launch with Trade Memory OFF entirely.** During apprenticeship, the review queue does the work Trade Memory would do: unknown formats and ambiguous lines go to a human, and the human's rulings accumulate as history in the audit trail regardless. Extraction is somewhat slower to improve, but nothing is lost — the recorded rulings can seed the pattern library later, after the doctrine is settled.

**Options:** (a) adopt as drafted — learning starts with Lane C, bounded from birth; (b) defer entirely — Lane C builds with the component disabled behind the doctrine's absence; adopt before enabling; (c) adopt storage-and-inspection only, defer reliance — patterns are recorded but never used, a middle path that mostly buys review time.

**The real deadline is not the build.** The freeze-snapshot rule matters at the moment a worker is certified journeyman — that is when an unfrozen Trade Memory becomes a sanctioned drift channel (the memory audit's central finding). Decision needed **before the Receipt Agent's journeyman certification**, which is at minimum one full quarter of operation away.

**Blocks while held:** nothing on the critical path. Lane C builds with the component disabled.

## 3. RECOMMENDED SEQUENCE FROM HERE

1. **Start Lanes A and B now** — fully approved, first two merges, zero contact with any held item.
2. **Start Lane C's unblocked scope** — intake, evidence registration, parsers, validators, mileage worksheet, IFTA engine. Router last.
3. **Start Lane D on fixtures** — Fuel Spend and IFTA Position; Expense Summary waits for #3.
4. **Decide #2 and #3 before Lane C's router** — the first hold that will actually stop work.
5. **Decide #4 before the first merge into integration.**
6. **Decide #14 before Receipt Agent journeyman certification** — the most patient of the four.

No held item needs to be rushed today; every held item has a named deadline tied to a build event rather than a date. The build can begin this week without borrowing against any decision Mike hasn't made.

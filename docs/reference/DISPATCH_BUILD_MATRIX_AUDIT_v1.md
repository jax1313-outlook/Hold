# DISPATCH_BUILD_MATRIX_AUDIT_v1

Auditor role: build matrix auditor and integration-risk reviewer
Scope: parallel-build safety for Matrix Group 1; merge order; sandbox strategy; validation gates
Date: 2026-08-03
Authority: Advisory only. Mike Zachary is final authority.

---

## THE GOVERNING FINDING

The fences already defined — constitutions, contexts, responsibilities, boundaries, memory rules, workflows, approval gates — are **behavioral** fences. They keep workers from drifting at runtime. They do not keep parallel *builds* from colliding, because builds collide on a different surface: **data contracts**. Two lanes that each "improve" the Fuel Record schema mid-build, or invent their own queue-item format, will produce four components that pass their own tests and fail each other.

Parallel building is safe exactly to the degree that the interfaces between lanes are frozen before the lanes start. The good news: five audits have already specified nearly everything that needs freezing. The missing fence is one short document set — call it the **Contract Pack**:

1. The three record schemas — Fuel, Expense, Evidence (round 4, Sections 2–4), plus the mileage record contract.
2. The queue item contract — what goes into the Manager's decision/review queue, and what "resolved" means.
3. The archive/evidence interface — register document, get evidence ID, retrieve by ID.
4. The physical/logical path mapping (the round-3 naming fix) — with **configurable roots**, so sandbox builds write to test roots, never to the real D:\ trees.
5. The closed expense-category vocabulary (Mike authors it).
6. The audit-log entry format (round 3, Section 3) — shared plumbing, written once, used by every lane.

Freeze the Contract Pack first — a few focused sessions, all writing — and Matrix Group 1 becomes contract-coupled instead of code-coupled, which is the only kind of parallel that survives Murphy.

One more reality check that shapes everything below: this is a one-person shop. Parallel lanes here means parallel build sessions, but **integration attention is a single human resource**. The fences can make four lanes safe to *build*; nothing can make four simultaneous *merges* safe for one integrator. Hence: build in parallel, merge strictly one at a time.

## 1. RECOMMENDED MATRIX GROUP 1

**Q1 — Is Matrix Group 1 safe for simultaneous build? Conditionally yes** — safe after the Contract Pack freezes, unsafe before. All four builds touch disjoint code with narrow, specifiable seams.

**Q2 — Should Librarian be built first alone?** Not alone-to-completion — that serializes everything behind the least urgent half of the Librarian (truth promotion, governance workflows). But the Librarian's **evidence spine** (archive-on-registration, hashing, evidence indexing, basic retrieval) should get a short head start, because two other lanes stub against it and the sooner the real thing exists, the shorter the stubs live. Split the Librarian build: Evidence Spine now, leading; Truth Governance continuing in parallel, merging later.

**Q3 — Manager parallel with Librarian? Yes.** Near-zero surface overlap: Manager touches routing and approvals; Librarian touches storage. Their only shared seams are the queue item contract and the audit-log format — both in the Contract Pack. Two Manager rules must be tested from day one because they are constitutional, not cosmetic: silence is never consent (no auto-approve on timeout, ever), and the full queue is always visible to Mike.

**Q4 — Receipt → IFTA parallel? Yes**, and it is the highest-value lane — the round-4 GO scope. It builds against two stubs: a dumb archive stub (Contract Pack item 3) until the Evidence Spine merges, and a primitive review inbox until the Manager queue merges. Mileage: per round 4, a human-entered mileage worksheet in the frozen schema keeps the IFTA half honest without waiting on Dispatch Ops tooling.

**Q5 — Reports parallel? Yes, as the trailing lane — and it is structurally the safest of the four.** Reports is read-only plus one write (the print queue); a component that writes almost nothing can break almost nothing. It builds against fixture data conforming to the frozen schemas. Its one real risk is fidelity, not integration: its numbers must match the source records exactly, which is why its final validation gate needs real extracted data and therefore why it merges last.

**Q6 — Publisher in Group 1? No.** The stated reason is correct and the round-2 boundary work agrees: Publisher needs Library retrieval and Manager routing to exist and be trustworthy, and it carries the lowest current business value of the seven workers. Confirmed wait.

**Q7 — Intelligence in Group 1? No.** "Should not become a shallow sweeper" is exactly the round-2 finding — Intelligence is the vaguest worker and the one whose deep-source inspection design must precede its constitution, let alone its code. It also cannot exist safely before its single customer (the Manager's decision queue) is real. Confirmed wait.

**Q13 — Minimum viable Matrix Group 1:** two lanes — Receipt→IFTA chain + Librarian Evidence Spine. That pair delivers the round-4 v1 (the quarterly pain-killer) with a real audit trail under it. If Manager lags, a primitive inbox suffices for one quarter.

**Q14 — Maximum safe Matrix Group 1:** all four lanes (Evidence Spine + Manager queue + Receipt→IFTA + Reports), Contract Pack frozen, merges serialized. Five or more lanes (adding Publisher or Intelligence) is past the line — not because the fences fail, but because the integrator is one person and merge debt compounds faster than build progress.

## 2. BUILDS THAT SHOULD WAIT

Publisher (needs Library + Manager routing mature; lowest current value). Intelligence (needs deep-source inspection design; needs the decision queue to exist; highest vagueness = highest drift risk if built early). Accounting Agent (round-2 tripwire not tripped). QuickBooks live connector (round 4: the queue plus manual posting works; the connector layer slots in later without re-plumbing). Dispatch Ops full build — note it is *absent from the matrix* and that is fine for this group, but it is the next build after Group 1 lands, because Cost Per Mile, real mileage records, and the Loads report all wait on it.

## 3. PARALLEL SAFETY ASSESSMENT

| Lane | Collision surface | Stubs needed | Safety |
|---|---|---|---|
| A. Librarian Evidence Spine | archive interface, audit log | none | HIGH — everyone depends on it, it depends on nothing |
| A2. Librarian Truth Governance | promotion workflow, Library index | none, but merges after A | MEDIUM — wait for round-3 doctrine fixes to land in writing first |
| B. Manager Work Queue | queue contract, audit log | none | HIGH — small, self-contained |
| C. Receipt→IFTA | all three schemas, archive stub, queue stub | archive, review inbox | HIGH with frozen contracts; LOW without |
| D. Reports | read-only over schemas; print queue | fixture data | HIGHEST — read-only by constitution |

The one lane with a genuine precondition beyond the Contract Pack is A2: building truth-promotion before the round-3 memory fixes (naming/mapping, read-write matrix, Trade Memory freeze semantics) are adopted in writing would encode ambiguity into the most permanent component. Evidence Spine doesn't wait; Truth Governance does.

## 4. DEPENDENCY MAP

```
Contract Pack (freeze first — all writing, no code)
    │
    ├────────────┬─────────────┬──────────────┐
    ▼            ▼             ▼              ▼
A. Evidence   B. Manager    C. Receipt→IFTA   D. Reports
   Spine         Queue         (stubs for A,B)   (fixtures)
    │            │             │              │
    │            │   C swaps in real A ◄──────┤ D validates against
    │            │   C swaps in real B        │ real C data at gate
    ▼            ▼             ▼              ▼
A2. Truth Governance (after round-3 fixes adopted; merges after A)

Waiting room: Publisher ── needs A2 + B mature
              Intelligence ── needs B + deep-source design
              Dispatch Ops ── next group; unblocks mileage, CPM, Loads report
```

## 5. MERGE ORDER (Q8)

One at a time, each validated before the next begins:

1. **Librarian Evidence Spine** — the floor everything stands on.
2. **Manager Work Queue** — the escalation channel; C's inbox stub retires here.
3. **Receipt Agent** — producers before consumers; its archive stub retires here.
4. **IFTA Agent** — consumes C's records against the real spine and real queue.
5. **Reports** — last, because its gate requires real data from 3–4 to prove fidelity.
6. **Librarian Truth Governance** — whenever ready; it gates Publisher, not Group 1.

The rationale is uniform: every merge lands onto the thing it depends on, already validated. No big-bang merge day — merge day plural, small, boring, and boring is the goal.

## 6. VALIDATION GATES (Q11)

Every lane passes all six before its merge:

1. **Contract conformance** — outputs validate against the frozen schemas, byte-for-byte on shared fixtures. One conformance suite, generated from the Contract Pack, runs in every lane — this is the single cheapest Murphy insurance available.
2. **Golden regression** — the lane's fixed test set passes (Section 7). This same set becomes the worker's journeyman exam and permanent anti-drift suite (round 1).
3. **Boundary refusal** — the component demonstrably refuses out-of-scope operations: Reports attempting a write fails; IFTA attempting to modify a source record fails; queue attempting auto-approval fails. Test the fences, not just the features.
4. **Audit completeness** — every action produced a well-formed audit entry; sampled and verified.
5. **Human walkthrough** — Mike runs the workflow end-to-end on real documents in the sandbox and signs off. No component merges on green checks alone.
6. **Docs match as-built** — the worker's constitution/context reflect what was actually built; any divergence is resolved *in the documents* before merge, because the documents are the law.

## 7. TEST REQUIREMENTS (Q10)

**Evidence Spine:** immutability (modify-after-archive must fail); hash integrity round-trip; register→retrieve fidelity; document-level dedup by hash; retention class assignment; path mapping honored (writes land only under configured roots).
**Manager Queue:** full lifecycle (enqueue→route→decide→resolve); no auto-approve on timeout under any configuration; queue visibility completeness; audit entry per transition; escalation terminates correctly (round 2: one channel).
**Receipt Agent:** golden receipt set — 50 real documents with known-correct extractions (start collecting them now; they are the scarcest test asset and only Mike can bless them); sum validation catches seeded mismatches; dedup catches the same purchase arriving as receipt AND statement line; ambiguous-line quarantine routes the line, releases the rest; dual-record fuel emission with intact cross-links; provenance link present on every record, no exceptions.
**IFTA Agent:** known-quarter regression — one hand-computed quarter the agent must reproduce exactly; MPG band alarms fire on seeded gaps; each round-4 exception type detected from seeded data; source-immutability (the agent cannot alter an input record to balance a worksheet); rate-table version pinning.
**Reports:** determinism (identical inputs → identical output, repeatedly); fidelity (displayed totals equal source-record arithmetic exactly); displays stored IFTA values, never recomputes them; read-only enforcement; save-for-print archives the snapshot with template version + as-of stamp.

## 8. SANDBOX RECOMMENDATION (Q12)

**One repository, feature branches per lane, one integration branch — not a separate sandbox repo.** A second repo is where Murphy lives: histories diverge, there is no shared conformance suite, and the final "merge into Dispatch" becomes a transplant instead of a merge. The user's preferred protection (build → test → validate → then merge) is exactly right; implement it as:

- `main` — always releasable; nothing lands here except from integration, gated.
- `integration` — merges arrive one at a time in Section 5 order; the conformance suite and cumulative regression suites run here; a failed merge backs out cleanly.
- `build/librarian-spine`, `build/manager-queue`, `build/receipt-ifta`, `build/reports` — one branch per lane; each rebases from integration after every merge event so drift never exceeds one merge cycle.

Two hard rules: **sandbox code never touches real data roots** — all paths come from the Contract Pack mapping, and sandbox configuration points at test roots (this is the round-3 mapping fix paying for itself); and **a frozen contract changes only by Mike's decision, version bump, and same-day broadcast to every lane** — a schema change discovered mid-build is escalated, never quietly patched in one lane.

## 9. FINAL GO / NO-GO

**GO for parallel build — with the Contract Pack as the ignition key.**

Recommended sequence: freeze the Contract Pack (writing only — the six items in the Governing Finding, most already drafted across rounds 1–5); then launch the maximum-safe matrix: **Evidence Spine leading, Manager Queue and Receipt→IFTA in parallel, Reports trailing on fixtures**; merge one at a time in Section 5 order, each through the six gates; Publisher, Intelligence, Accounting, and the live connector stay in the waiting room behind their named tripwires.

Murphy's Law planning, summarized in one line each: contracts frozen before lanes open (collisions can't start), stubs kept dumb (divergence can't hide), merges serialized (failures can't stack), regression suites cumulative (yesterday's correctness can't silently break), sandbox roots isolated (a bad build can't touch a real receipt), and main always releasable (there is always a working system to retreat to).

This is the sixth audit in the series, and the first one where the answer is simply: the plan is sound — freeze the contracts and start building.

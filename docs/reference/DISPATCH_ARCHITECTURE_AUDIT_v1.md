# DISPATCH_ARCHITECTURE_AUDIT_v1

Auditor role: architecture auditor, responsibility mapper, system stress tester
Scope: Dispatch Core v1 pre-coding validation
Date: 2026-08-03
Authority: Advisory only. Mike Zachary is final authority.

---

## 1. VALIDATION SUMMARY

Direct answers to the sixteen questions.

**1. Is the worker catalogue complete enough for Dispatch Core v1?**
Almost. The seven-worker catalogue covers the governance, knowledge, and operations spine. Two responsibilities in the money path have no owner: invoicing / receivables (rate confirmation + POD → invoice → payment tracking) and the compliance calendar beyond IFTA (IRP, Form 2290, insurance renewals, maintenance intervals, driver files). Neither requires a new agent in v1 — both can be helper layers under Dispatch Ops or explicitly declared out of scope — but they must be declared one way or the other, or they will be absorbed informally by whichever agent is nearest, which is exactly the drift your doctrine exists to prevent.

**2. Are there too many agents?**
Not structurally, but too many for the first build wave. Publisher and Intelligence are the two least load-bearing workers for a transport operation's core. The revenue-critical chain is Dispatch Ops → Receipt → IFTA → Accounting. Recommendation: keep Publisher and Intelligence in the catalogue but sequence them after the operations chain is at journeyman.

**3. Are there too few agents?**
No. The gaps identified above are responsibility gaps, not agent gaps. Your own doctrine — Department → Journeyman Agent → Helper Layers — is the correct answer to them.

**4. Are any responsibilities overlapping?**
Yes, four material overlaps. (a) Manager as "external software bridge" vs. Receipt Agent pushing to the QuickBooks API — two owners of external integration. (b) Intelligence's "report" function vs. the Reports shared layer — one is interpretation, one is deterministic query, but the doctrine doesn't say so. (c) Publisher's "Version Controller-adjacent" intake/QC vs. Librarian's Version Controller role — asset versioning vs. knowledge versioning needs a drawn line. (d) Librarian as Truth Gatekeeper vs. Intelligence as analyzer/recommender — who promotes a finding into Memory is implied but not stated. Details in Section 3.

**5. Are any responsibilities missing?**
Yes: invoicing/AR, the compliance calendar, ownership of D:\Archive, ownership of the canonical data schemas (interface contracts between agents), a failure/exception doctrine, an audit-trail doctrine, and duplicate/idempotency handling in the Receipt flow. Details in Section 2.

**6. Is the Base Constitution strong enough to prevent drift?**
It is strong on authority and weak on drift. The authority block prevents insubordination; it does not prevent drift, because drift is rarely an agent claiming new authority — it is an agent's outputs slowly changing shape until downstream consumers break or humans stop trusting them. Drift prevention requires four things the doctrine doesn't yet have: (a) versioned interface contracts frozen with the worker, (b) a "journeyman exam" — a fixed regression test set a worker must pass before Freeze and continue passing after any change, (c) an operational definition of Freeze (pinned prompts, pinned model/config, pinned output schemas — not just intent), and (d) a change-control rule: who may amend a constitution, and that any amendment increments the version. Add these and the constitution becomes genuinely drift-resistant.

**7. Is the Manager too powerful, not powerful enough, or properly scoped?**
Properly scoped as foreman, routing authority, decision-queue manager, and attention protector. Over-scoped as "external software bridge." That one phrase is the seed of a super-agent: if all external I/O flows through the Manager, it accumulates every credential, every integration, and every failure mode, and becomes both a bottleneck and the single worker whose compromise or drift breaks everything. Fix: the Manager routes work and decisions, never data payloads; each integration is owned by the agent whose domain it serves (Receipt owns the QuickBooks push), or by a thin non-agent integration layer. Also add one explicit denial to the Base Constitution: the Manager may not create, modify, or retire workers — only Mike commissions workers.

**8. Is the Intelligence Agent deep enough as designed?**
It is the vaguest worker in the catalogue, and vagueness is where drift starts. "Observe, analyze, report, recommend. Must inspect deeper source material" is a good instinct but not a job description. Before its constitution is written, define: what sources it watches, on what cadence, what its deliverable types are (e.g., market brief, lane analysis, broker risk note), where deliverables go (the Manager's decision queue), and the hard boundary that Intelligence recommends and never executes.

**9. Is Publisher correctly scoped as production manager rather than creator?**
Yes, with one watch item: "First-Line Editor" is the creep vector. Editing must be defined as conformance checking (format, completeness, standards) rather than content generation, or the Publisher becomes a creator by accretion. Also reconsider its position in the v1 build order (see Q2).

**10. Is Librarian correctly assigned control over memory, retrieval, metadata, and truth promotion?**
Yes — this is the right consolidation, and having one Truth Gatekeeper is a strength. Three additions needed: (a) explicit promotion criteria — what evidence qualifies a claim for D:\Memory, (b) a demotion/correction path when promoted truth turns out wrong, and (c) ownership of D:\Archive. Right now Archive is a destination with no custodian; the Librarian is the natural owner of both History and Knowledge.

**11. Is Receipt Agent correctly designed as a multi-output transaction extractor?**
Yes — "a receipt is a container of business transactions" is the strongest single design decision in the document. Three gaps: (a) intake ownership is ambiguous (does Dispatch Ops feed it, or does it have its own intake for non-load expenses like parts and washes?), (b) no duplicate detection — the same receipt photographed twice becomes double-counted gallons and a wrong IFTA return, (c) no partial-extraction path — an unreadable receipt needs a human-review queue, not a guess.

**12. Is IFTA Agent correctly separated from Receipt Agent?**
Yes. Extraction is continuous clerk work; IFTA preparation is quarterly, jurisdiction-aware, and consequence-bearing. Different cadence, different failure modes, different approval weight — correct separation. However, the flow as drawn cannot produce an IFTA return: IFTA requires fuel purchased by jurisdiction AND miles traveled by jurisdiction. The diagram feeds the IFTA Agent fuel records only. Mileage-by-jurisdiction must flow from Dispatch Ops (route/trip data, or ELD data via it) into the IFTA Agent. This is the most concrete architectural defect in the document.

**13. Should Reports remain a shared layer rather than an agent?**
Yes, emphatically. Reports must be deterministic — same question, same data, same answer. Making it an agent injects nondeterminism exactly where trust requires none. The dropdown-driven, visual-first, print-on-request design is right for the user. One rule to add: Reports reads from governed storage only and never writes anything but the print queue.

**14. Is there a risk of overbuilding?**
Yes, and it is the near-term risk: eight constitutions and a full governance stack before a single receipt has been parsed. Mitigation is already in your doctrine — build one worker at a time. Sharpen it: write DISPATCH_BASE_CONSTITUTION_v1 plus ONE worker's full document chain, build that worker to journeyman, and only then template the pattern for the next. Do not write all seven worker constitutions up front; the first build will teach you things that would otherwise force seven rewrites.

**15. Is there a risk of underbuilding?**
Yes, in a specific place: the governance layer is well-developed while the data layer is undefined. There are no canonical schemas (what is a Fuel Record? a Load? an Expense Record?), no interface contracts between agents, no failure doctrine, no audit-trail doctrine, no idempotency rules. Constitutions govern behavior; schemas govern truth. Both layers are required before code.

**16. What should be fixed before coding begins?**
See Section 8. The blocking items are: interface contracts/schemas, the Manager bridge ambiguity, the IFTA mileage input, the exception/escalation doctrine, and enumerated hard approval gates.

---

## 2. MISSING COMPONENTS

1. **Interface contracts (blocking).** Versioned schemas for every record that crosses an agent boundary: Fuel Record (Receipt → IFTA), Expense Record (Receipt → QuickBooks), Evidence Record (Receipt → Library), Load/Trip Record (Dispatch Ops → IFTA mileage, Reports). These are as constitutional as the constitutions — freeze them with the workers that emit them.
2. **Mileage-by-jurisdiction feed to IFTA (blocking).** Dispatch Ops → IFTA Agent trip/jurisdiction data. Without it, IFTA Agent cannot do its job.
3. **Failure and exception doctrine (blocking).** Manufacturing floors have an andon cord. Define: on failure, a worker stops, quarantines the work item, and posts to the Manager's decision queue; retry rules; what a worker may never do silently (skip, guess, discard).
4. **Enumerated hard approval gates (blocking).** The doctrine requires approval gates per worker but never lists the non-negotiables. Minimum set in the Base Constitution: any government filing (IFTA), any money movement or accounting write (QuickBooks), any deletion or demotion of promoted Memory, any constitution change.
5. **Audit-trail doctrine.** A governed workforce needs a work-order log: every agent action recorded (who, what, input, output, timestamp) in an append-only location. IFTA records carry a multi-year retention requirement — this is legal exposure, not bookkeeping preference.
6. **Archive ownership and retention rules.** D:\Archive has no custodian and no retention policy. Assign to Librarian; set retention minimums driven by tax/IFTA requirements.
7. **Duplicate/idempotency rules in the Receipt flow.** Same receipt submitted twice must be detected, not double-booked.
8. **Invoicing / receivables responsibility.** Rate con + POD → invoice → factoring/payment tracking. Assign as a Dispatch Ops helper layer or declare out of scope for v1 — but declare it.
9. **Compliance calendar responsibility.** IRP, 2290, insurance, maintenance intervals, driver qualification files. Same treatment: helper layer or explicit deferral.
10. **Backup doctrine.** Operations, Archive, and Memory all live on one physical drive. One drive failure destroys the living system, its history, and its knowledge simultaneously. Off-drive (ideally off-site) backup is required before the system holds anything that matters.

## 3. OVERLAPS / CONFLICTS

1. **Manager "external software bridge" vs. per-agent integrations.** The Receipt flow shows Receipt Agent → QuickBooks API, but the Manager is named the external software bridge. Pick one model. Recommended: Manager routes decisions, agents (or a thin non-agent integration layer) own their domain integrations.
2. **Intelligence "report" vs. Reports layer.** Write the distinction into both documents: Reports = deterministic queries over structured operational data; Intelligence = interpretation and recommendation over external and internal sources. Intelligence may cite Reports output; it never replaces it.
3. **Publisher QC/intake vs. Librarian versioning.** Draw the line at promotion: Publisher owns work-in-progress assets and their intake/QC; the moment an asset is accepted as done, custody transfers to the Librarian. Two version domains, one handoff point.
4. **Librarian Truth Gatekeeper vs. Intelligence analysis.** Make the promotion workflow explicit: Intelligence (and others) produce candidate knowledge; only the Librarian promotes to D:\Memory; contested promotions go to the Manager's decision queue; Mike breaks ties.

## 4. BOUNDARY RISKS

1. **Manager scope creep** via the bridge role (Q7) — highest structural risk in the document.
2. **Publisher "editor" creep** from conformance checking into content creation (Q9).
3. **Receipt intake ambiguity** — if intake ownership is undefined, both Dispatch Ops and Receipt Agent will grow competing intake behaviors.
4. **Reports layer write access** — bound it to read-only plus print queue, or every agent will eventually treat it as a convenient side door for output.
5. **Worker commissioning** — no rule currently prevents the Manager (or any worker) from spawning helpers. State in the Base Constitution that only Mike commissions, modifies, or retires workers and helper layers.

## 5. MEMORY MODEL RISKS

1. **No read/write matrix.** The doctrine says each worker must know what memory it may use, but no document defines which agents may read or write Operations, Archive, and Memory. Draw the matrix; default deny; Librarian is sole writer to Memory and Archive.
2. **No promotion/demotion lifecycle.** Operations → Archive (when? by whom?) and candidate → Memory (on what evidence?) are undefined transitions.
3. **Truth conflicts.** No rule for what happens when an agent's observation contradicts promoted Memory. Recommended: the agent flags, the Librarian adjudicates, Memory is never silently overwritten.
4. **No Memory schema.** Knowledge entries need minimum metadata: source, date, promoting authority, confidence, supersedes-link. Without it, retrieval decays into a pile of files.
5. **Single-drive co-location.** Covered in Section 2, item 10 — it is also a memory-model risk: History and Knowledge share the fate of the Living System.

## 6. WORKFLOW RISKS

1. **IFTA missing its second input** (mileage by jurisdiction). Blocking.
2. **No failure path anywhere in the Receipt flow.** Every arrow in the diagram is a happy path. Each hop needs a defined failure branch ending at a human queue.
3. **No idempotency.** Re-submission, retries after failure, and duplicate photos all produce double entries under the current design.
4. **Approval gates unplaced.** The flow shows IFTA packages going to human approval (good) but is silent on QuickBooks writes. An automated write into accounting without a gate is the fastest way to lose trust in the whole system.
5. **Manager decision-queue overload.** As attention protector, the Manager needs triage rules (urgent/today/whenever) or the queue becomes the very cognitive load the system exists to remove.
6. **Print queue is well-designed** — deferred printing from the workstation fits the operating reality. No change needed.

## 7. AGENT DRIFT RISKS

1. **Freeze is aspirational, not operational.** Define frozen = pinned instructions + pinned configuration + pinned output schemas + passing regression suite. Any change to any pinned element = version bump + re-certification.
2. **No journeyman exam.** Promotion from Apprentice to Journeyman should require passing a fixed test set of real historical cases (e.g., 50 real receipts with known-correct extractions). The same set becomes the anti-drift regression suite forever after.
3. **Intelligence Agent under-specification** — the least-defined worker will drift first.
4. **Output-format drift.** The most common real-world drift is not role expansion but output shape mutation, which silently breaks downstream consumers (Receipt → IFTA especially). Interface contracts (Section 2, item 1) are the control.
5. **Constitution amendment is uncontrolled.** Add a change-control clause: only Mike amends; every amendment increments the version; workers cite the version they were certified against.

## 8. SUGGESTED CORRECTIONS (pre-coding)

**Blocking — resolve before any code:**
1. Write the interface contracts: Fuel Record, Expense Record, Evidence Record, Load/Trip Record. Version them.
2. Add Dispatch Ops → IFTA mileage-by-jurisdiction to the flow.
3. Resolve the Manager bridge conflict: Manager routes decisions, not data; integrations live with domain owners.
4. Write the failure/exception doctrine (stop, quarantine, escalate; no silent skip/guess/discard).
5. Enumerate hard approval gates in the Base Constitution: government filings, accounting writes, Memory demotion, constitution changes.

**Strongly recommended — resolve before first worker reaches Journeyman:**
6. Define Freeze operationally and institute the journeyman exam / regression suite.
7. Draw the storage read/write matrix; assign Archive to the Librarian; set retention rules.
8. Add duplicate detection and a human-review queue to the Receipt flow.
9. Add the audit-trail (work-order log) doctrine.
10. Establish off-drive backup for all three storage roots.

**Scoping decisions:**
11. Sequence the build: Base Constitution → Dispatch Ops (or Receipt) → Receipt → IFTA → Librarian → Manager helpers → Intelligence → Publisher. Write one worker's full document chain at a time; template from the first, don't pre-write all seven.
12. Assign or explicitly defer invoicing/AR and the compliance calendar.
13. Sharpen the Intelligence Agent job description before its constitution is drafted.

## 9. GO / NO-GO RECOMMENDATION

**CONDITIONAL GO.**

The architecture is sound at its core. The bounded-worker philosophy, the constitutional hierarchy, the document-before-code creation order, the Apprentice→Journeyman→Freeze maturity model, Receipt-as-transaction-container, the Receipt/IFTA separation, and Reports-as-deterministic-layer are all correct decisions, and no redesign is warranted. There is no fatal flaw.

But do not start coding yet. The system is currently governed above and undefined below: the constitutions say who may act, while nothing says what the data is, what happens on failure, or which actions are hard-gated. Resolve the five blocking corrections — interface contracts, the IFTA mileage input, the Manager bridge ambiguity, the failure doctrine, and the enumerated approval gates. That is roughly a few focused working sessions of writing, not a redesign.

Then: GO — for DISPATCH_BASE_CONSTITUTION_v1 plus one worker built to journeyman, before any other worker's documents are written.

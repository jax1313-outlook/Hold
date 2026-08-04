# DISPATCH_MEMORY_AUDIT_v1

Auditor role: memory architecture auditor
Scope: Company/Trade memory split, Library/Memory/Archive tiers, storage placement, lifecycle, metadata
Date: 2026-08-03
Authority: Advisory only. Mike Zachary is final authority.

---

## 1. MEMORY ARCHITECTURE VALIDATION

**Headline finding before the twelve answers:** the memory model is conceptually sound but has one defect that must be fixed before it hardens into folder structures — the word "Memory" now means three different things. (1) D:\Memory, a physical root, which round 1 called "Knowledge." (2) Memory the logical tier, defined here as "Working Knowledge." (3) Company Memory, an umbrella term that includes the Archive and the Library. On top of that, the Company Memory location list mixes physical paths (D:\Memory, D:\Archive) with logical stores (Library, Archive) without saying where Library physically lives or whether "Archive" the tier is the same thing as D:\Archive the folder. This is not pedantry: every worker constitution will cite these names, and an ambiguous name in a constitution becomes an ambiguous boundary in behavior. Fix: publish a one-page mapping — each logical tier (Library, Memory, Archive, Workspace/Operations, Trade Memory) mapped to exactly one physical root, and retire the standalone word "Memory" in favor of tier names. This is a naming defect, not a design flaw; no redesign is warranted.

**Q1. Is the Company Memory vs Trade Memory split sound?**
Yes — it is the memory-model twin of your bounded-worker philosophy, and it matches the manufacturing analogy precisely: Company Memory is the engineering document set; Trade Memory is the machinist's own calibration notes. It prevents workers from privatizing company knowledge and gives Apprentice→Journeyman a mechanism. Three things are missing from the split as written: (a) Trade Memory has no physical home — assign each worker one inspectable location; private to the worker's function but never secret from Mike or the audit trail. (b) Trade Memory has no freeze semantics — see Risk 2 below; this is the most important gap in the doctrine. (c) There is no promotion path from Trade to Company Memory — when the Receipt Agent learns "this fuel-card vendor puts DEF on page 2," that lesson may be company-valuable; without a promotion path (worker proposes → Librarian routes → human approves → enters Company Memory), useful knowledge stays trapped inside one worker and dies with its freeze snapshot.

**Q2. Is Library / Memory / Archive separation clear enough?**
Conceptually yes — Approved Truth / Working Knowledge / History is a clean triad, and "Archive ≠ Trash" is exactly right. Operationally no, for two reasons: the physical mapping above, and the absence of transition rules. Nothing says when working knowledge becomes approved truth, what evidence that promotion requires, or when living material crosses into Archive. Tiers without transitions become three piles with vibes. Section 5 supplies the lifecycle.

**Q3. Is Librarian assigned proper governance over approved truth?**
Yes, with the round-2 settlement carried forward: the Librarian is the sole writer to the Library, custodian of the Archive, and executor of promotion rules that Mike authors — enforcer, never legislator. One addition for the memory model: the Librarian does not own or edit Trade Memory (it belongs to the worker's function) but must be able to *inspect* it and must operate the Trade→Company promotion path. And one pleasing consequence worth writing down: the constitutions themselves are Company Memory — current versions live in the Library as approved truth, superseded versions go to Archive. The system's own law obeys the system's own memory model.

**Q4. Should Receipt source documents live in Memory, Archive, or both?**
Archive — and never Memory. A scanned fuel-card statement is not working knowledge; it is evidence. The original goes to Archive immediately upon registration, immutable from that moment, because it is the leaf of the audit chain an IFTA auditor will walk (worksheet → fuel record → source image) and IFTA source documents carry a four-year retention requirement. The Evidence Record — the metadata pointer with extraction linkage — is registered in the Library's index so the document is *findable* through approved retrieval. So: the document lives in Archive, its catalogue entry lives in the Library, nothing lives in Memory. "Both" is the right answer only in that split sense.

**Q5. Should structured transaction records live in Memory, Archive, or Dispatch Operations?**
Dispatch Operations while their reporting cycle is open; Archive when it closes. Fuel Records for the current quarter are operational data being consumed by the IFTA Agent — they live in Operations. The moment the quarter's return is approved and filed, those records archive together with the return package as one sealed bundle. Expense Records live in the Operations staging area (Accounting deferred, per round 2) and archive once posted. Transaction records never belong in Memory: they are facts about business events, not knowledge about how to work. Rule of thumb worth writing into the doctrine: **transactions are operational until their period closes, then they are history; they are never knowledge.** Every record carries a link back to its Evidence Record so the provenance chain never breaks.

**Q6. Should Reports outputs live in Workspace first, Archive after completion, or Library after approval?**
All three, in that order, with steeply decreasing frequency. Default: a viewed report is ephemeral workspace output and simply evaporates — no storage, no clutter. If print/save is selected: the generated artifact goes to the print queue and then to Archive, because a generated report is a historical snapshot ("fuel, this quarter, as of Aug 3") the moment it is rendered. Library only in the rare case a human explicitly approves a report as a standing reference document. The critical rule is the one your doctrine already gestures at: **a report is a snapshot of data, never a source of truth.** Answers are regenerated from governed data; nobody cites last month's PDF as authority. That single rule prevents the entire class of stale-report-as-truth failures.

**Q7. Should generated PDFs be treated as Archive, Library, or Publisher output?**
None of the above as a category — a PDF is a container, not a class. Route by content, not by file extension: an IFTA package PDF lives in Operations while pending approval and archives after filing; a saved report PDF archives as a snapshot; a Publisher-produced asset PDF follows the production flow into the Library upon approval. And a boundary note from the round-2 audit applies here: rendering PDFs is a shared capability (a layer), not a Publisher monopoly. The moment "it's a PDF, send it to the Publisher" becomes the rule, the Publisher has become the company printer — a role expansion nobody chose.

**Q8. Is Trade Memory safe if workers learn format patterns?**
Yes — format patterns ("Pilot statements carry DEF on page 2," "this vendor uses MM/DD/YY") are precisely what Trade Memory is *for*, and they are the mechanism by which the Receipt Agent earns journeyman rank. Two guards make them safe. First, validation before reliance: during apprenticeship a proposed pattern is confirmed by human review before the worker may depend on it. Second, graceful degradation: a pattern is a hypothesis, not a law — when a statement stops matching a learned pattern, the worker flags and queues; it never force-fits data into the pattern. The dangerous pattern type is not format knowledge but *validity shortcuts*: "this vendor never has meal items, so skip meal classification." That is a learned decision to stop checking, and it rots silently. Write the distinction into the doctrine: **Trade Memory may optimize HOW a worker checks; it may never conclude WHETHER to check.**

**Q9. What prevents Trade Memory from becoming unauthorized policy?**
Today: a declaration ("may not expand authority"), and declarations don't enforce themselves. Five mechanisms do: (1) **Inspectability** — Trade Memory lives in a known per-worker location in readable form; Mike and the audit trail can see it; secret memory is where policy hides. (2) **A closed type system** — Trade Memory entries must be one of: format pattern, exception pattern, efficiency note, validated shortcut. Anything that reads as a rule about what *should be done* ("always route X to Y," "skip approval when...") is policy, is rejected at write time, and is escalated as a proposal instead. (3) **The journeyman exam as drift detector** — the regression suite from round 1 catches behavioral change regardless of which memory caused it. (4) **Freeze snapshots Trade Memory** — see Risk 2. (5) **The promotion path as pressure valve** — a legitimate rule-shaped lesson has somewhere lawful to go (proposal → Librarian → Mike → Company Memory), so there is no justification for smuggling it into private notes.

**Q10 & Q11 (metadata).** See Section 3.

**Q12. What is missing from the memory model?**
In priority order: the physical/logical mapping and the "Memory" naming fix; Trade Memory's physical home, inspection rights, and freeze semantics; the lifecycle transition rules (Section 5); a deletion and retention doctrine — who may delete anything, ever (recommended: no worker may delete; the Librarian archives; only Mike destroys, and never inside statutory retention windows — IFTA four years, IRS-relevant records up to seven); the provenance-chain requirement (every derived record links to its source, unbroken from IFTA worksheet line to receipt image); supersession rules for the Library (truth is never edited in place — a new version supersedes, the old version archives with a supersedes-link, so the Library has no history and the Archive has all of it); the storage read/write matrix (flagged in round 1, still open — which worker may read/write which tier, default deny); and the backup doctrine (flagged in round 1, still open — all tiers on one physical drive means Company Memory in its entirety shares one point of failure; this is now a *memory-model* defect, not just an infrastructure note).

---

## 2. RISKS

1. **Naming collision hardening into structure.** Three meanings of "Memory" today become miswired folder trees, misaddressed constitutions, and workers writing to the wrong tier tomorrow. Cheapest fix in the whole system; do it first.
2. **Trade Memory as the sanctioned drift channel.** Freeze aims to stop behavioral change; Trade Memory exists to cause it. As written, a frozen worker with an open Trade Memory is not frozen — it is drifting with permission. Fix: journeyman certification snapshots Trade Memory as part of the freeze; after freeze, Trade Memory is read-only, and new lessons are queued as proposals for periodic human-approved incorporation followed by re-certification against the regression suite. This is the most important single correction in this audit.
3. **Provenance chain breaks.** If a Fuel Record cannot walk back to its source scan, the IFTA position is unsupportable in audit. The chain must be a required field, not a convention.
4. **Report snapshots masquerading as truth.** An old saved report contradicting fresh data is inevitable; the "snapshot, never source" rule plus regeneration-by-default disposes of it.
5. **Deletion without doctrine.** "Archive ≠ Trash" is a value statement; without a written rule it will be violated the first time disk space runs low. No worker deletes; only Mike destroys; statutory windows are inviolable.
6. **Trapped knowledge.** Without the Trade→Company promotion path, each worker's lessons die at its freeze, and worker N+1 re-learns worker N's vendors from scratch.
7. **Single-drive fate-sharing.** Truth, knowledge, history, and the living system on one drive: one failure erases the company's mind. Third consecutive audit flagging this; it should not survive to a fourth.
8. **Librarian throughput.** Sole-writer-to-Library is correct governance and, at this company's scale, no bottleneck — noted only so that if intake volume ever grows tenfold, the answer is helper layers under the Librarian, never write access for other workers.

## 3. MISSING METADATA FIELDS

**For retrieval (every Company Memory item):**
record ID; title/description; content class (fuel record, expense record, evidence record, template, procedure, narrative, asset, report snapshot, constitution...); tier (Library / Operations / Archive); source/provenance link; date created; date of subject matter (the business date, distinct from creation date); approval status, approver, approval date; version and supersedes-link; related entities (vendor, truck, driver, load, broker, jurisdiction, quarter); format; retention class; tags.

**For audit trail (every worker action, append-only):**
actor (worker name + worker version + constitution version certified against); action type; timestamp; input record refs; output record refs; approval reference where a gate was crossed (who approved, when, which gate); Trade Memory dependency note (if the action relied on a learned pattern, name it — this is what makes Q9 auditable); outcome (completed / flagged / quarantined); hash or version link to prior state for anything modified.

The two lists serve different masters — retrieval serves the worker and Mike; audit serves the future auditor and the post-incident investigation — and both must be mandatory at write time, because metadata added later is metadata invented later.

## 4. RECOMMENDED STORAGE LOCATIONS BY DATA TYPE

| Data type | Active home | On cycle close / approval | Library role |
|---|---|---|---|
| Receipt source documents (scans, statements, e-invoices) | Intake staging (Operations), minutes only | Archive immediately on registration; immutable | Evidence Record indexed in Library catalogue |
| Fuel Records | Operations (open quarter) | Archive, sealed with the filed IFTA package | none |
| Expense Records | Operations staging (Accounting deferred) | Archive after posting to QuickBooks | none |
| Evidence Records (pointers + extraction linkage) | — | permanent | Library index entry |
| IFTA worksheets, exception lists, report packages | Operations while pending human approval | Archive after filing, with approval mark | none |
| Reports — viewed only | Workspace, ephemeral | discarded | none |
| Reports — print/save selected | Print queue | Archive as dated snapshot | only by explicit human approval as reference doc |
| Approved templates, procedures, narratives, graphics, videos, workflows, rules | Library (current version) | superseded versions → Archive | this IS the Library |
| Constitutions & doctrine documents | Library (current version) | superseded versions → Archive | approved truth about the system itself |
| Trade Memory | one inspectable location per worker (e.g., a Workers\<name>\TradeMemory root under Operations) | snapshot at freeze; read-only after | never in Library; promoted lessons enter Library as company knowledge via the Librarian |
| Audit / work-order logs | Operations (rolling), append-only | roll into Archive on schedule | none |

## 5. RECOMMENDED LIFECYCLE: DRAFT → CANDIDATE → APPROVED → ARCHIVED

**Knowledge and asset track (things that can become approved truth):**
1. **Draft** — created in the Operations workspace by the originating worker. Mutable. Owned by the originator. Invisible to retrieval.
2. **Candidate** — work complete, submitted for approval; custody passes to the approval route (Publisher's routing for produced assets; the Manager's decision queue otherwise). Frozen as submitted — revisions spawn a new draft version rather than editing the candidate. Still not truth; still not retrievable as truth.
3. **Approved** — a human approves; the approval mark (who/when/what gate) is recorded; the Librarian — and only the Librarian — promotes the item into the Library with full retrieval metadata. From this moment it is immutable: change means supersession, and supersession means a new item pointing back at this one.
4. **Archived** — on supersession, expiration, or explicit retirement, the Librarian moves the item to Archive with its retention class. Append-only. No worker deletes; only Mike destroys, outside statutory windows.

**Transactional track (records that are facts, not truth-claims — they skip the Library):**
1. **Extracted** — Receipt Agent produces the record in Operations, provenance-linked, transaction-dedup checked.
2. **Validated** — passes contract checks (or is flagged to the human queue; a flagged record never proceeds silently).
3. **Consumed** — read by its customer (IFTA Agent, QuickBooks posting) during the open period.
4. **Sealed** — the period closes with human approval (return filed, statement posted); the whole bundle archives together.

The two tracks are the answer to a question the doctrine hadn't asked yet: not everything passes through the Library, but everything ends in the Archive.

## 6. FINAL MEMORY MODEL RECOMMENDATION

**Validated, with one naming defect and one doctrinal gap to close before coding.**

The two-type split (Company vs Trade) is sound and is the correct memory-model expression of the bounded-worker philosophy. The three-tier triad (Library / Memory / Archive) is conceptually right. The Receipt memory case routes correctly. The Reports memory case is correct once "snapshot, never source" is written down. No serious flaw requiring redesign exists.

Before coding: (1) publish the physical/logical mapping and retire the bare word "Memory" — tier names only; (2) give Trade Memory a home, an inspection right, a closed type system, and above all freeze semantics — a frozen worker's Trade Memory is snapshotted and read-only, with a proposal queue for post-freeze lessons; (3) adopt the lifecycle in Section 5 and the mandatory metadata in Section 3; (4) write the deletion/retention doctrine; (5) resolve the two survivors from round 1 that are now memory-model defects, not infrastructure notes: the read/write matrix and the single-drive backup.

Do those and the memory model will be the strongest layer of the architecture — which is fitting, because in a system built on documents-before-code, memory *is* the system.

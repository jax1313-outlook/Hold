# DISPATCH_REPORTS_DESIGN_REVIEW_v1

Reviewer role: human-centered operations design reviewer
Scope: Reports layer — architecture, menu design, v1 scope, storage, print queue
Date: 2026-08-03
Authority: Advisory only. Mike Zachary is final authority.
Language rule honored: "Reports" throughout. The word "analytics" appears nowhere below this line.

---

## 1. REPORTS ARCHITECTURE VALIDATION

**Q1 — Layer, not agent: yes, settled and re-affirmed.** Reports must be deterministic — same question, same data, same answer, every time. An agent adds judgment exactly where trust requires none. The two bounding rules from earlier audits carry forward as the layer's whole constitution: Reports reads governed storage only, and writes nothing except the print queue.

**Q2 — Dropdowns: right design, with two refinements.** Four dropdowns, a checkbox, and one button is the correct amount of interface for this audience and for gloved fingers on a tablet. Refinements: (a) add a **Recents row** — one-tap chips above the dropdowns for the last three reports run. An owner-operator asks the same three questions over and over ("fuel today," "expenses this month," "IFTA position"); after the first week, most sessions should be one tap, zero dropdowns. (b) Make the Filter dropdown **context-sensitive** — show Truck only when the fleet has more than one unit, show State on fuel/IFTA reports, show Category on expense reports. A filter that never applies is clutter wearing a dropdown costume.

**Q3 — Visual-first, print-later: yes, this matches how the business actually runs.** Quick answers happen on a tablet in or near the truck; printing happens later at the workstation. "No PDF unless asked" is also the round-3 memory doctrine (ephemeral by default) expressed as interface. Keep it exactly as designed.

**Q4–Q6 — prebuilt reports and filters: see Sections 3 and 4.** One governing principle first: **the menu must never offer a report whose data doesn't exist yet.** The proposed Report Type list includes Customers, Brokers, and Operations — but v1 data (per the round-4 workflow audit) is fuel records, expense records, IFTA worksheets, and whatever load records Dispatch Ops produces. A report that comes back empty or half-right even once teaches the user the system can't be trusted, and for this audience the Reports screen IS the system — it is the face by which Dispatch will be judged. Ship four report types with complete data behind them; add Brokers and Customers when Ops data matures.

**Q7 — storage:** live answers are ephemeral workspace output and evaporate; saved/printed reports go to the print queue and Archive (Section 6). Never Memory — a report is not knowledge. Never Library — with one exception, Q9.

**Q8 — should saved reports become Archive automatically? Yes.** The clean mechanics: selecting Save For Printing writes the dated, immutable snapshot to Archive *immediately*; the print queue holds a reference to that archived copy, not a second copy. Printing changes nothing about custody; clearing the queue deletes nothing but the queue entry. One artifact, one home, one reference. This also means the print queue can be rebuilt or emptied fearlessly — the Archive copy is the real record.

**Q9 — should approved report templates live in Library? Yes, and this is quietly important.** A template — the layout plus the query definition — is approved truth about how a question gets answered. Version it in the Library under Librarian custody. Then determinism becomes provable: any archived report is fully specified by template version + data as-of date. When a template changes, old snapshots still cite the version that made them.

**Q10 — should Publisher format formal reports? Not operational ones.** The Reports layer renders its own answers; putting an agent in the render path makes a deterministic layer depend on a nondeterministic worker — latency and drift for zero gain. The Publisher enters only when report *content* becomes a *published asset*: a formal package for a bank, an insurer, a broker prospect, a government proposal. Then the archived report snapshot is an approved input (retrieved through the Librarian, per round 2) and the Publisher's normal production flow applies. Boundary in one line: **Reports serves answers; Publisher produces assets.**

**Q11 — calculate or display? Both, split by a bright line.** Reports may perform *arithmetic*: sum, average, count, group-by over stored records — deterministic aggregation is what a report is. Reports may never perform *domain judgment*: no tax rates, no classifications, no accrual logic, no reclassifying an expense on the fly. Domain-computed values (IFTA tax positions above all) are calculated once by the owning agent, stored, and merely displayed by Reports. The test: if a number could ever differ between the Reports screen and the owning agent's worksheet, the design has failed — two screens, one source.

**Q12 — IFTA and Reports:** the IFTA Agent computes and stores worksheet values; Reports displays the stored quarter-to-date position. Three display rules: label everything pre-filing as **"Prepared — estimate, not filed"**; show the exception count inline ("3 exceptions unresolved — totals may change") so a clean-looking number never hides a dirty pipeline; and after filing, the report shows the approved, sealed numbers and says so. Reports never runs its own tax math — that is Q11's bright line applied to the one place it could do real damage.

**Q13 — fuel today on a tablet:** lead with the number, not a chart. One big figure — **$487.32** — readable at arm's length in daylight glare; gallons directly beneath it in half the size; one comparison line ("yesterday $512 · 7-day avg $455"); a small by-truck or by-state breakdown below the fold only if the fleet warrants it; a data-freshness line at the bottom ("through today 2:15 PM · 1 receipt pending review"). High contrast, big touch targets, no chrome, loads instantly. A chart is optional decoration under the answer — never the answer.

**Q14 — smallest useful Reports v1: see Section 8's final paragraph.** One sentence: three report types (Fuel, Expenses, IFTA Position) over the round-4 data spine, six date ranges, context-sensitive Truck/State/Category filters, the Recents row, and the save-to-Archive print queue.

## 2. RECOMMENDED V1 MENU

```
Reports

[ Fuel Today ]  [ Expenses This Month ]  [ IFTA Position ]     ← Recents / one-tap chips

▼ Report Type
    Fuel
    Expenses
    IFTA
    Loads                (include only if Ops load records exist at launch)

▼ Date Range
    Today
    Yesterday
    This Week
    This Month
    Last Month
    Custom

▼ Filter               (context-sensitive; hidden when nothing applies)
    Truck              (only if fleet > 1 unit)
    State              (Fuel and IFTA reports)
    Category           (Expense reports)

☐ Save For Printing

[ Run Report ]
```

Changes from the proposed menu, with reasons: Customers, Brokers, Operations removed from v1 (no complete data behind them yet — restore when Ops matures); **Sort By dropped from v1 entirely** — a visual answer has no sort order, and tabular print views can default to date; every dropdown removed is a gift to the person in the truck. Recents row added. Data-freshness line always shown on results.

## 3. RECOMMENDED V1 PREBUILT REPORTS

1. **Fuel Spend** — total $ and gallons for the period; by state and by truck when filtered; price-per-gallon trend line on week/month views.
2. **Expense Summary** — total by category (the closed vocabulary from round 4) for the period; category drill-down shows the line items.
3. **IFTA Position** — quarter-to-date: gallons and miles by jurisdiction, fleet MPG, estimated net tax per jurisdiction from stored IFTA Agent values; exception count; "Prepared — estimate, not filed" label.
4. **Cost Per Mile** — the owner-operator's flagship number: (fuel + expenses) ÷ miles for the period, with the three inputs shown so the number is never a black box. Include in v1 only if mileage records are flowing reliably; otherwise it is the first v1.1 report.
5. **Loads This Week/Month** — count, status board, revenue if Ops records carry it. Only if the data exists at launch.

Five is the ceiling. Every additional prebuilt report in v1 is a bet against simplicity with someone else's attention.

## 4. RECOMMENDED FILTERS

**Essential in v1:** Date Range (the six proposed presets are exactly right); Truck/unit (only when fleet > 1); State/jurisdiction (fuel and IFTA); Expense Category (expenses).

**Deferred:** driver, broker, customer, vendor, payment method, load type, free-text search, any compound/multi-select filtering, saved custom filter sets. Each one returns only when a real repeated question demands it — filters are added by evidence of need, never by symmetry ("we have the field, so add the filter" is how crowded menus happen).

## 5. PRINT/SAVE QUEUE RECOMMENDATION

Keep the design as proposed — generate, queue, print later from the workstation — with these mechanics: Save For Printing archives the snapshot immediately (immutable, dated, template-version-stamped) and enqueues a *reference*; the queue lives in Dispatch Operations as plain infrastructure (a layer's holding area, per round 2 — no agency, custodian: the layer itself, contents disposable); queue entries show report name, period, and saved date, and can be printed, reprinted, or cleared without ever touching the Archive copy; nothing else in the system may write to the queue. The queue is the Reports layer's single permitted write, and it stays that way.

## 6. STORAGE RECOMMENDATION

| Artifact | Home | Notes |
|---|---|---|
| Live visual answer | workspace, ephemeral | evaporates on navigation; never stored |
| Saved/printed report | **Archive**, immediately on save | immutable dated snapshot; print queue holds a reference |
| Print queue | Dispatch Operations (infrastructure) | disposable references only |
| Report templates (layout + query definitions) | **Library**, versioned, Librarian custody | approved truth about how questions are answered |
| Report-derived published assets | Publisher flow → Library | only when a human commissions a formal document |
| Anything in Memory | **nothing** | a report is a snapshot, never knowledge |

The round-3 rule remains the load-bearing wall: **a report is a snapshot of data, never a source of truth.** Regenerate from governed data; never cite last month's snapshot as authority.

## 7. RISKS

1. **Trust is single-use.** The first wrong or half-empty number on the Reports screen costs adoption of the entire platform, because for this audience the Reports screen is Dispatch. Mitigations: never ship a report type without complete data behind it; always show the freshness line and pending-review count; show IFTA numbers with their exception count attached.
2. **Creep toward a BI platform.** "Just one more filter / one more dropdown / one more report type" is how this screen becomes the crowded top menu the doctrine forbids. The evidence-of-need rule (Section 4) is the guard; Mike owns additions the way he owns the expense vocabulary.
3. **Divergent numbers.** If Reports ever recomputes what an agent already computed, two screens will eventually disagree and both lose credibility. Q11's bright line — arithmetic yes, domain judgment never — is the guard; IFTA is where it matters most.
4. **The side-door risk.** Any worker that finds writing to Reports convenient has found an ungoverned output channel. Read-only plus print queue, enforced in the constitutions, permanently.
5. **Stale snapshots resurfacing as truth.** Someone will one day wave a printed March report against a live April screen. The template-version + as-of-date stamp on every printed page is what settles the argument in ten seconds.
6. **Performance decay.** Quarterly archives grow; "Fuel Today" must stay instant at year three. Not a v1 problem, but the template definitions should assume period-scoped queries from day one so it never becomes one.

## 8. FINAL RECOMMENDATION

**Validated — the Reports doctrine is the most user-shaped piece of the Dispatch architecture, and it is right.** Layer not agent: correct. Dropdowns not crowded menus: correct. Visual first, print later, no unrequested PDFs: correct, and consistent with the memory doctrine besides. The design's instincts — prebuilt over configurable, simple over complete, the trucker's vocabulary over the developer's — are exactly the instincts that make operational software get used instead of abandoned.

Adjustments, all subtractive or clarifying: trim v1 to the report types whose data spine exists (Fuel, Expenses, IFTA, conditionally Loads); drop Sort By from v1; make filters context-sensitive; add the Recents row; archive-on-save with the queue holding references; templates versioned in the Library; and write the two bright lines into the layer's one-page charter — *reads governed storage, writes only the print queue* and *arithmetic yes, domain judgment never.*

**Smallest useful Reports v1:** Fuel Spend, Expense Summary, and IFTA Position over the round-4 data spine, six date presets, three context-sensitive filters, a Recents row, the freshness line, and Save For Printing feeding an archive-backed queue. That is a Reports layer a working owner-operator will actually open every morning — which is the only metric that matters.

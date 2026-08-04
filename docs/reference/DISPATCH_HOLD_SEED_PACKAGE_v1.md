# DISPATCH_HOLD_SEED_PACKAGE_v1

Purpose: the initialization plan for the **Hold repository** — a clean construction repository, intentionally empty, not a clone of Dispatch. This package assumes nothing exists: no files, no contracts, no constitutions. It defines what must be created, in what order, before any lane session opens.
Contains: structure and sequence only. No implementation code. No application files.
Authority: Mike Zachary is final authority. Approval status of 2026-08-03 applies throughout (#2, #3, #4, #14 HELD).

## 1. REQUIRED FOLDER STRUCTURE

Created at seed, before anything else. Folders marked (empty) are seeded with a `.gitkeep` and populated only by their owning lane — the seed creates the fence lines; the lanes build inside them.

```
Hold/
├── README.md                     what this repo is, what it is not, where the law lives
├── .gitignore                    *.db, __pycache__/, .venv/, *.pyc, sandbox artifacts
├── config/
│   ├── config.schema.json        (contract copy — see §3)
│   └── sandbox.config.json       sandbox roots ONLY; no production config may exist in Hold
├── contracts/                    THE LAW — read-only to all lanes (see §3)
├── docs/
│   ├── governance/               constitutions, doctrines, registers (see §2)
│   ├── reference/                the audit series + blueprint + execution package (read-only)
│   ├── decisions/                DECISION_LOG.md + one file per resolved hold
│   └── lanes/
│       ├── A/NOTES.md            seeded empty with the required section headings
│       ├── B/NOTES.md
│       ├── C/NOTES.md
│       └── D/NOTES.md
├── src/
│   └── dispatch/
│       ├── common/               (empty — Lane A)
│       ├── evidence/             (empty — Lane A)
│       ├── queue/                (empty — Lane B)
│       ├── receipt/              (empty — Lane C)
│       ├── ifta/                 (empty — Lane C)
│       └── reports/              (empty — Lane D)
├── library_seed/
│   ├── Constitutions/            populated from docs/governance at seed (what ships to LIBRARY)
│   ├── Templates/Reports/        (empty — Lane D)
│   ├── Vocabulary/               (empty — HELD #3; contains only HOLD.md marker)
│   └── RateTables/                seeded with the current IFTA quarter table + source note
├── tests/
│   ├── conformance/              (empty — Lane A builds the shared suite)
│   ├── stubs/                    (empty — Lanes B/C add their consumer stubs)
│   ├── fixtures/                 (empty — Lane D)
│   ├── golden/
│   │   ├── receipts/             (empty — Mike feeds; blessing is his alone)
│   │   └── ifta/                 (empty — the hand-computed quarter lands here)
│   ├── lane_a/  lane_b/  lane_c/  lane_d/   (empty — owning lanes)
└── tools/                        (empty — Lane A and Lane C add their tools)
```

Two placement rules: the Hold repository lives OUTSIDE the three operational roots (never under `D:\Dispatch Operations`, `D:\Memory`, or `D:\Archive` — a construction site is not the living system); sandbox data roots (e.g. `D:\DispatchSandbox\{Operations,Library,Archive}`) live OUTSIDE the repository and are named only in `sandbox.config.json`.

## 2. REQUIRED GOVERNANCE DOCUMENT STRUCTURE

`docs/governance/` at seed:

| Document | Content at seed | Status |
|---|---|---|
| `DISPATCH_BASE_CONSTITUTION_v1.md` | All APPROVED provisions: authority hierarchy, storage mapping (#1), failure doctrine (#5), deletion & retention (#6). Contains a marked, empty section: **"HARD APPROVAL GATES — HELD (#4), reserved, adoption pending"** so the held content has a named landing place and nobody mistakes absence for rejection. | Partially adopted |
| `LIBRARIAN_CONSTITUTION_v1.md` | Authority block + approved boundary clause (#10) + Evidence Spine responsibilities/workflow distilled from blueprint 4.1. | Required before Lane A |
| `MANAGER_CONSTITUTION_v1.md` | Authority block + approved clause (#7) + queue responsibilities/workflow from blueprint 4.2, incl. silence-is-never-consent and full-visibility rules. | Required before Lane B |
| `RECEIPT_CONSTITUTION_v1.md` | Authority block + approved clause (#12) + buildable-scope workflow; explicit HELD markers on routing (#2/#3) and Trade Memory (#14). | Required before Lane C |
| `IFTA_CONSTITUTION_v1.md` | Authority block + approved clause (#13) + worksheet/exception/package workflow per blueprint 3.5. | Required before Lane C |
| `REPORTS_CHARTER_v1.md` | Reports is a layer, not an agent — no constitution; a one-page charter: reads governed storage, writes only the print queue; arithmetic yes, domain judgment never; snapshot never source. | Required before Lane D |
| `APPROVAL_REGISTER.md` | The 14 items, status, date, and source link for each. The single place approval truth lives; updated only by Mike's decisions. | Required at seed |
| `MEMORY_DOCTRINE_v1.md` | Tier definitions and mapping (#1), lifecycle (draft→candidate→approved→archived; extracted→validated→consumed→sealed). Marked, empty section: **"TRADE MEMORY — HELD (#14), reserved."** | Required before Lane A |

This satisfies the locked rule — *No Constitution = No Agent* — for exactly the workers Group 1 builds, and no others. `docs/reference/` receives read-only copies of the seven audits, DISPATCH_BUILD_BLUEPRINT_v1, DISPATCH_MATRIX_EXECUTION_PACKAGE_v1, and DISPATCH_HOLD_IMPACT_AND_BRIEFS_v1. `docs/decisions/DECISION_LOG.md` is seeded with four open entries: #2, #3, #4, #14.

## 3. REQUIRED CONTRACT STRUCTURE

`contracts/` at seed, with a naming convention that makes legal status visible in the filename:

**Frozen (in force — suffix `.schema.json`, header block carries `"status": "FROZEN v1.0"`, freeze date, and "changes only by Mike's decision + version bump + same-day notice"):**
- `config.schema.json` (blueprint 1.1, approved #1)
- `evidence_record.schema.json` (blueprint 1.2)
- `mileage_record.schema.json` (blueprint 1.2)
- `queue_item.schema.json` (blueprint 1.3)
- `audit_entry.schema.json` (blueprint 1.6)

**Draft (NOT law — suffix `.DRAFT.json`, header carries `"status": "DRAFT — HELD"` and the hold number):**
- `fuel_record.DRAFT.json` (held on #2 — the D1 cross-link field is the open question)
- `expense_record.DRAFT.json` (held on #2 and #3 — cross-link + category validation open)

**Held-absent (a marker, not a file that could be mistaken for content):**
- `expense_vocabulary.HOLD.md` — one paragraph: the vocabulary is held (#3), lives in the Library as versioned data when approved, and no category list may be embedded anywhere in code meanwhile.

**Register:** `contracts/CONTRACT_REGISTER.md` — one row per contract: name, version, status (FROZEN / DRAFT-HELD / HELD-ABSENT), freeze or hold date, hold number, change history. The register is the index a build session checks before trusting any schema.

## 4. REQUIRED INITIALIZATION SEQUENCE

1. Create the empty repository at its location outside the operational roots; default branch `main`.
2. Make the five seed commits on `main`, in the §5 order. Nothing else touches `main` directly after commit S5, ever.
3. Apply branch rules: `main` accepts merges only from `integration`; `integration` accepts merges only lane-by-lane, in the blueprint 4.5 order, each after its six validation gates and Mike's sign-off. (On a solo local repo these are discipline rules recorded in the README as much as tooling rules — write them down either way; the README is the fence.)
4. Create `integration` from `main`.
5. Create the four lane branches from `integration`: `build/librarian-spine`, `build/manager-queue`, `build/receipt-ifta`, `build/reports`.
6. Create the sandbox data roots on disk (empty directories, outside the repo) exactly as named in `sandbox.config.json`.
7. Verify the seed against the §6/§7 checklists. Only then may Packet A's session open.

## 5. REQUIRED FIRST COMMITS

Five commits, on `main`, in this order — each leaves the repository in a legally coherent state:

- **S1 — "Seed: structure and fences."** Folder tree (§1), `.gitignore`, `README.md` (what Hold is; the binding rules from the Execution Package: contracts are read-only law, lanes build only in their allowed files, held decisions stop threads, sandbox only; the branch discipline).
- **S2 — "Governance: constitutions and registers."** Everything in §2, including the APPROVAL_REGISTER reflecting 2026-08-03 and the DECISION_LOG with four open holds.
- **S3 — "Contracts: freeze the in-force set; mark the held drafts."** Everything in §3, including the CONTRACT_REGISTER. From this commit forward, `contracts/` changes only by Mike's decision.
- **S4 — "Reference: the audit record."** The audit series, blueprint, execution package, and hold briefs into `docs/reference/` — so every build session cites the same canonical texts instead of remembering them differently.
- **S5 — "Config: sandbox environment."** `config/sandbox.config.json` naming the sandbox roots; the current-quarter IFTA rate table with its source note into `library_seed/RateTables/`.

Branch creation (steps 4–5 of §4) follows S5. First lane commit happens on `build/librarian-spine`, never on `main`.

## 6. DOCUMENTS THAT MUST EXIST BEFORE LANE A STARTS

From §2: `DISPATCH_BASE_CONSTITUTION_v1.md` (approved provisions incl. mapping, failure, deletion) · `LIBRARIAN_CONSTITUTION_v1.md` · `MEMORY_DOCTRINE_v1.md` · `APPROVAL_REGISTER.md`.
From §3: `config.schema.json` · `evidence_record.schema.json` · `mileage_record.schema.json` · `queue_item.schema.json` (Lane A's retrieve must know the exception-item shape it enqueues) · `audit_entry.schema.json` · `CONTRACT_REGISTER.md`.
From elsewhere: `config/sandbox.config.json` · `docs/lanes/A/NOTES.md` placeholder · Packet A from the Execution Package (in `docs/reference/`).
**Explicitly NOT needed by Lane A:** the fuel/expense drafts, the vocabulary, the hard-gates section, the Trade Memory section — Lane A touches none of them.

## 7. DOCUMENTS THAT MUST EXIST BEFORE LANE B STARTS

Everything in §6 (the seed makes this automatic), plus: `MANAGER_CONSTITUTION_v1.md` · Packet B. Lane B's stub signatures derive from the frozen `audit_entry` and `evidence_record` contracts already present.
For completeness — **before Lane C:** §6 plus `RECEIPT_CONSTITUTION_v1.md`, `IFTA_CONSTITUTION_v1.md`, the two `.DRAFT.json` files (Lane C's provisional IFTA input adapter reads the draft's in-force fields and must see the DRAFT stamp), the rate table, and Packet C. Golden sets may start empty; they must be non-empty before Lane C's *gate*, not its start. **Before Lane D:** §6 plus `REPORTS_CHARTER_v1.md` and Packet D.

## 8. DOCUMENTS THAT CAN BE DEFERRED

Deferred with a named arrival trigger — absence is intentional, not oversight:

| Deferred document | Arrives when |
|---|---|
| Frozen `fuel_record.schema.json` / `expense_record.schema.json` | #2 (and #3 for category validation) decided → Packet C-2 opens with the freeze as its first act |
| `expense_vocabulary` v1 (Library data file) | #3 decided |
| Base Constitution HARD GATES section | #4 decided — required before the first merge into `integration` (docs-match-as-built gate) |
| MEMORY_DOCTRINE Trade Memory section | #14 decided — required before any journeyman certification (Packet C-3) |
| `PUBLISHER_CONSTITUTION_v1` / `INTELLIGENCE_CONSTITUTION_v1` / `DISPATCH_OPS_CONSTITUTION_v1` | their build tripwires (Publisher: Library + routing mature; Intelligence: deep-source design exists; Ops: Matrix Group 2) |
| Truth-promotion / retrieval-governance doctrine detail | before the Librarian Truth Governance lane (post-Group-1 merge 6) |
| Report template files, fixtures, stubs, golden expected-outputs | created by their owning lanes inside their allowed files — the seed never fabricates lane work |
| Production `dispatch.config.json` | cutover, after merge 5, created by Mike — it never exists in Hold before then |

---

**Seed completion test:** the repository is correctly seeded when a Lane A session, given only Packet A and this repository, can answer every question it will have — where the law is, which schemas are frozen, which are held, where it may write, and where it must stop — without asking a human anything except for approvals the doctrine already routes to Mike.

*End of DISPATCH_HOLD_SEED_PACKAGE_v1. Structure and sequence only; no implementation code; nothing herein overrides DISPATCH_BASE_CONSTITUTION_v1 or proceeds past a hold.*

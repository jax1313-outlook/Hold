# OCR_VISION_EXTRACTION_DOCTRINE_v1

**Status:** Approved architectural direction, 2026-08-04. Applies to the
future IFTA Clerk architecture (`docs/ifta-clerk/IFTA_CLERK_BLUEPRINT_v1.md`)
and any future document-processing workflow built within Dispatch —
not IFTA-specific. Operates under `CONSTITUTION.md` and
`DISPATCH_BASE_CONSTITUTION_v1.md`, alongside `RECEIPT_CONSTITUTION_v1.md`,
which this doctrine names but does not amend.

## Core principle

OCR / vision extraction is a data-capture layer. It captures information
from business documents. It is not an agent, not a decision maker, not a
source of truth, not an authority layer. It does not create business
records independently, does not bypass validation, does not bypass
evidence registration, and does not bypass human authority.

## Authoritative record

The Evidence Record — the original scanned receipt, image, PDF, or
document — is always authoritative. OCR output is derived data. OCR
output may be wrong. Evidence remains authoritative regardless.

## Architecture

```
Document
  -> Evidence Spine
  -> Hash
  -> Audit
  -> Archive Link
  -> OCR / Vision Extraction
  -> Validation Layer
  -> Fuel Record / Expense Record / future business records
  -> Business Clerk
  -> Review Dashboard
  -> Human Approval
  -> Archive Package
```

Extraction happens only after evidence is already hashed, archived, and
audited — never before. A record is created only after extracted data
passes an explicit validation layer — never directly from raw extraction
output.

## Capture once, use many times

A receipt is captured once: evidence registered once, OCR reads once,
Fuel/Expense records created once. The same verified data may then
support IFTA, accounting, tax reporting, audits, expense tracking,
business analytics, and future workflows — the receipt is never
re-processed by separate systems for each downstream use.

## Exception handling

Insufficient OCR confidence never becomes a guess. The system does not
invent values and does not silently continue: it creates an exception,
creates a queue item, and requests human review. The system prefers a
**Known Unknown** over a **Confidently Wrong** answer.

## The IFTA Clerk rule

The IFTA Clerk — and, by this doctrine, any future business-record
consumer — consumes verified, validated extracted data. It never
consumes raw OCR output directly. OCR output must pass validation before
it becomes usable business data.

## Human authority

The OCR layer may never approve filings, approve payments, approve
records, modify doctrine, modify profiles, change calculations, or
create authority of any kind. Human approval remains required
throughout, unchanged by this doctrine.

## Compliance check against what's already built (2026-08-04)

This doctrine was written after, not before, Lane C's receipt pipeline —
worth checking honestly rather than assuming either agreement or drift.
Verified directly against the real code:

| Principle | Status | Evidence |
|---|---|---|
| Evidence registered before extraction | **Already compliant** | `dispatch.receipt.intake.IntakePipeline._process_one_file()`: `self._spine.register(...)` runs first; extraction (`self._extract(...)`) only runs after registration succeeds. The module's own docstring names this ordering as a direct requirement of contract 1.4. |
| Validation layer sits between extraction and record creation | **Already compliant** | `dispatch.receipt.validators.validate_document()` runs structural, sum, confidence, and dedup checks on every extracted line, deterministic or vision-sourced alike, before `dispatch.receipt.router.Router.route_line()` is ever called. No code path creates a `FuelRecord`/`ExpenseRecord` directly from extractor output. |
| Insufficient confidence -> exception, not a guess | **Already compliant** | `validators.py`'s `low_confidence` check (`DEFAULT_CONFIDENCE_THRESHOLD = 0.75`) quarantines any line below threshold with a real `QuarantinedLine`; `intake.py`'s `_quarantine_line()` creates a real Queue item for every one. No line below threshold is ever routed. |
| OCR never creates a record independently | **Already compliant** | `ClaudeVisionExtractor.extract()` returns plain line dicts only — it has no reference to `EvidenceSpine`, `Router`, or `QueueStore`, and cannot write anything itself. |
| OCR never bypasses human authority | **Already compliant** | Nothing under `dispatch.receipt.extraction` imports `dispatch.queue.store.QueueStore.approve/reject/resolve`, `dispatch.ifta.package`, or anything else with approval/seal authority. |
| Capture once, use many times | **Already compliant, by construction** | `EvidenceSpine.register()` deduplicates by `file_hash` (a re-registered identical file returns the existing record, flagged `duplicate_document`, never re-extracted); the resulting `FuelRecord`/`ExpenseRecord` rows are read — never re-derived — by Reports, the IFTA worksheet engine, and now the IFTA UI alike. |

**The one real gap is not architectural — it's operational.** Vision
extraction has never run against a live credential in any environment
this project has used (`ClaudeVisionExtractor.__init__` raises
`VisionExtractionUnavailable` immediately when `api_key` is falsy, and no
`ANTHROPIC_API_KEY` has existed anywhere this system has run). Every
scanned/photographed receipt this project has ever processed has
therefore quarantined by design, exactly as this doctrine requires for
an uncertain input — not a violation of the doctrine, but a reminder
that "OCR reads a photograph" remains unverified against a real
credential, not just undoctrined.

## Relationship to `IFTA_CLERK_BLUEPRINT_v1`

This doctrine formalizes and slightly refines that blueprint's own
architecture: the blueprint's step 5 ("IFTA workspace") and step 7
("review dashboard") sit downstream of an explicit **Validation Layer**
this doctrine names as its own architectural stage — already
implemented as `validators.py`, not previously called out as a named
layer in the blueprint's own diagram. No contradiction; this doctrine is
the more precise statement and should be treated as authoritative where
the two describe the same architecture.

## Amendment history

- 2026-08-04: Adopted, in full, as directed. Compliance check performed
  against the real, already-merged Lane C pipeline the same day.

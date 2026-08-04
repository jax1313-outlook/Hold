# expense_vocabulary — HELD (#3)

**Status: HELD. This is a marker, not a data file.** No category list may be
embedded anywhere in code while this hold is open. When approved, the
vocabulary ships as versioned data in `library_seed/Vocabulary/` (Library,
Librarian custody), never in source.

## What is actually decided vs. not

**Decided (worker boundary clause #12, approved):** the vocabulary is
closed, and Mike owns it — the Receipt Agent may never extend it.

**Not decided:** the list's contents.

## Draft candidate list (NON-BINDING)

`DISPATCH_BUILD_BLUEPRINT_v1` Part 1.5, tagged `[MIKE APPROVES — he may
add/remove before freeze]` (i.e. drafted, not yet law):

```
fuel · reefer_fuel · def · meals · oil_additives · parts_maintenance ·
truck_wash · parking · tolls · scale_tickets · permits_fees · supplies ·
misc
```

**This is the blueprint author's draft, not an adopted list.** No lane
may treat it as final, embed it, or validate against it until it carries
a real freeze stamp in `contracts/CONTRACT_REGISTER.md`.

## How Mike is asked to decide (per `DISPATCH_HOLD_IMPACT_AND_BRIEFS_v1` Brief #3)

Three tests per candidate category:
1. Would you want QuickBooks or a report to slice on it? If not, fold it
   into a broader one.
2. Will a receipt line land in it at least monthly? If not, `misc` covers
   it.
3. Can a clerk assign it without judgment? If assigning it requires
   knowing *why* something was bought, it's too clever for extraction —
   keep the category physical, not intentional.

**Cost asymmetry:** adding a category later is a cheap version bump — old
records stay valid. Renaming, merging, or splitting later is expensive.
When in doubt, leave it out; `misc` plus the review queue is the escape
valve.

**Decision deadline:** before Lane C's router work begins (same deadline
as #2).

# WAFD ONE 10.0.0 RC128 — Deep QA Correction

Focused reliability review over RC127.

## Corrections
- Fixed the optional-items MultiCheck edge case so removing the final add-on cannot leave a stale higher price.
- Added server-side refusal to create a project when a selected add-on has no reference price.
- Verified operating-cost creation contains one packaging-labour row only (no double charge).
- Enforced authority food-supervisor approval in the direct daily-stage API before delivery.
- A fully received day stays `Received` until cleanup and the daily authority report are completed, then becomes `Closed`.

## QA scope
- Python compilation.
- JavaScript syntax validation.
- JSON metadata parsing.
- Patch-list module existence.
- DocType child-table and Select metadata consistency.
- Print Format mapping consistency for Iftar reports.
- Archive hygiene (no Python cache/temp files).

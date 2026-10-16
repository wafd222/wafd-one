# WAFD ONE 10.0.0 RC368 — Iftar Workflow Focused Corrections

## Scope
- Changes are confined to WAFD Iftar project creation/pricing and Iftar role portals. No unrelated modules or business data are changed.

## Changes
- The editable wizard price is now explicitly the VAT-inclusive standard base price. It remains stable while the selected package changes.
- Final sale price is computed from the base plus selected paid add-ons and the Iftar + Zamzam surcharge. The surcharge is applied both when the Zamzam package is selected and when the Zamzam replacement toggle is enabled. Switching back to Standard Iftar clears the package extras and restores the base.
- Project creation sends the base and final price as separate values; the server no longer derives the base by subtracting extras from the final price.
- VAT-inclusive gross, VAT portion, and net revenue now use a shared rounding rule, regression-tested against the 300 × SAR 8.50 and 500 × SAR 9.00 examples.
- Legacy records with an empty/zero base default safely to SAR 9 instead of compounding a previously calculated surcharge.
- The external read-only monitoring page now displays supervisor evidence photos already returned by its project-scoped API.
- The Project Manager project card no longer repeats vehicle-trip details already available in operational stages.

## Validation
- Python syntax compilation, JavaScript syntax validation, JSON parsing, ZIP integrity, and focused arithmetic/contract tests were run locally.
- Live Frappe Cloud permissions, database transitions, PDF generation, and mobile browser behavior require staging credentials/environment and were not simulated as live success.

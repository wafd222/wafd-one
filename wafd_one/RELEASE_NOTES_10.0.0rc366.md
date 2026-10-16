# WAFD ONE 10.0.0 RC366 — Iftar Editable Price Calculation Fix

## Focused changes
- Fixed the Iftar project creation save path so the VAT-inclusive selling price entered in step 2 is preserved after server-side validation.
- The default remains SAR 9.00. Paid add-ons are accounted for when deriving the project's standard base price, so the project's normal recalculation continues to produce the entered final selling price.
- Project revenue, VAT extracted from gross revenue, net revenue and expected profit continue to calculate from the saved final sale price and total meals.

## Scope protection
- Based on the prior RC365 candidate; functional source change is limited to `wafd_one/iftar_pro.py`. Version metadata and release notes were updated for this release.
- No hotel, contract, inventory or other unrelated workflow was intentionally changed.

## Validation
- Python source compilation, JavaScript syntax check, JSON syntax checks, ZIP integrity check, and price arithmetic smoke tests.
- Live Frappe Cloud/browser workflow has not been executed in this environment and must be verified in staging before production use.

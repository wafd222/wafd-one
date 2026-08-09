# WAFD ONE 10.0.0 RC146 — Final QA Report

Static and package-level QA performed before release packaging:

- Python compile validation for all application `.py` files.
- JSON parse validation for all application `.json` files.
- JavaScript syntax validation with Node.js for all application `.js` files.
- Patch-module path validation for every active entry in `wafd_one/patches.txt`.
- DocType controller presence validation for non-child-table DocTypes where a controller is expected.
- Version consistency validation (`pyproject.toml` and `wafd_one/__init__.py`).
- VAT invariant review: invoice gross retained, project/management revenue net of VAT, profit calculated from net revenue.
- Known example verified mathematically: SAR 575 gross = SAR 500 net + SAR 75 VAT; SAR 500 net − SAR 103 cost = SAR 397 profit; margin = 79.4%.
- Iftar invariant review: SAR 9.00 VAT-inclusive standard selling price; Zamzam cost-only at SAR 1.50; VAT extracted using 15/115 for Iftar profitability.
- Workflow invariant review: existing Production/Packaging/Loading/Delivery documents are opened rather than duplicated after progression.
- ZIP integrity validation after packaging.

Runtime database behavior still requires the normal Frappe Cloud `Migrate Site` and one end-to-end smoke test because the local QA environment does not contain the user's live Frappe database.

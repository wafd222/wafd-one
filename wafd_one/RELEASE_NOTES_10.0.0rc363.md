# WAFD ONE 10.0.0 RC363 — Iftar Focused Changes

## Included changes (Iftar Sa'im only)
- Added an editable project-level standard meal base price, defaulting to SAR 9.00 inclusive of VAT. The calculated sale price remains a separate read-only value and approved add-ons are applied on top of the configured base price.
- Extended the contracting-authority monitoring data with per-table-owner handover rows sourced from the daily supervisor reports, including location, delivered quantity, supervisor, delivery photo, recipient signature, and timestamp where recorded.
- Added separate authority-monitoring stage indicators for table-owner handover, meal distribution, and tablecloth raising.
- Changed the authority report action from immediately opening print to an interactive preview with scrollable content, zoom controls, back, print, and share actions.
- Added a controlled driver/vehicle reassignment action for Iftar trips before delivery proof is recorded; trip quantities and existing delivery history are preserved. The kitchen workflow also exposes this action after loading has been approved.
- Added responsive styling for owner handover records and delivery evidence on mobile.

## Scope protection
Only Iftar project pricing and the Iftar authority viewer/data provider were edited in this candidate. No hotel workflow or unrelated application module was intentionally changed.

## Validation completed
- Python syntax compilation for modified Python files.
- JavaScript syntax checks for modified JavaScript files.
- JSON syntax validation for the Iftar Project DocType.
- Archive integrity check before delivery.

## Deployment verification still required
This is a source candidate, not a verified Frappe Cloud deployment. Real site migration, role/permission behavior, existing-project price defaults, existing-project price defaults, project-manager and kitchen-role permission behavior for reassignment, role consolidation across all Iftar screens, full end-to-end authority report images, and all-device preview behavior require staging tests before production deployment.

# WAFD ONE 10.0.0 RC364 — Focused Iftar Sa'im fixes

## Changes limited to Iftar Sa'im
- Added an editable standard meal base price, default SAR 9.00 VAT-inclusive, with the calculated sale price and VAT/profit figures recalculated from the configured base.
- Added read-only authority records for each table owner, with location, supervisor, delivered quantity, delivery time, delivery photo and recipient signature when recorded.
- Added separate authority progress indicators for table-owner handover, meal distribution, and tablecloth raising.
- Changed the authority report action to open the same approved “WAFD Iftar Official Daily Report” print format used by the project-management workflow, preserving all existing stages, delivery evidence photos, table-owner photos/signatures, approval, and stamp. The preview provides scroll, zoom, back and print controls; sharing downloads/shares a PDF rendered from that same official report.
- Made driver/vehicle reassignment available from the kitchen workflow after loading, and from project-manager monitoring, only before delivery proof/arrival; quantity and history are preserved and the assigned driver login is synchronized.
- Kept kitchen preparation and vehicle assignment in one workflow so a separate delivery-supervisor screen is not required for the kitchen supervisor to prepare and load vehicles.

## Scope protection
The package was rebuilt from the unchanged RC362 baseline backup. Only Iftar project pricing, Iftar stage portal data, Iftar team UI, the Iftar authority-viewer UI, package version metadata, README, and release notes are included as intentional changes. Hotel workflow and unrelated modules were not intentionally modified.

## Validation
- Python source compilation and JavaScript syntax checks.
- JSON syntax validation for the Iftar Project DocType.
- ZIP integrity and package-diff review.
- Existing RC362 backup remains a separate, unchanged file.

Frappe Cloud staging and live browser verification are still required before production deployment.

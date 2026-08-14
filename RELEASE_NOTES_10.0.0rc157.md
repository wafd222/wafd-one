# WAFD ONE 10.0.0 RC157 — Final Role & UI Hardening

RC157 is a focused stabilization release built on RC156. It does not restart or redesign the previously validated operational cycle.

## Included fixes

- Production Supervisor now has read-only access to Daily Meal Plans while retaining the controlled ability to create Production Batches.
- Delivered/cancelled Daily Meal Plans are protected from ordinary edits.
- Financial fields on Daily Meal Plans, Daily Meal Plan rows, Catering Projects and Project Service rows are moved to permission level 1 and exposed only to authorized management/finance roles.
- Executive dashboard access is restricted server-side and at Page metadata level to management/finance/audit roles.
- Shared WAFD ONE workspace no longer exposes privileged administration, launch-center, document-studio, print-settings, Iftar, invoice or payment shortcuts to operational users.
- Project-created Hotel Undertakings automatically populate beneficiary name and nationality from the linked Mission, with server-side fallback on save.
- Delivery Note print template now includes the delivery photo when attached, while preserving receiver signature and hotel stamp support.
- Delivery Trip timing calculation now sets actual timestamps before calculating transit duration, derives planned arrival from service time minus delivery lead minutes, and avoids leaving valid trip duration at zero because of calculation order.
- RC156 consolidated role permissions are reapplied after stale Custom DocPerm cleanup so manual test overrides do not remain authoritative.
- Historical completed projects are not rewritten by this migration.

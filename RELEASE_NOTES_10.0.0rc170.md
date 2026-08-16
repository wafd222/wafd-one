# WAFD ONE 10.0.0 RC170 — Client Portal Route Fix

## Fixed
- Corrected the Frappe website-page location for the external client portal.
- `/wafd-client` now routes to the portal page after login instead of returning **Page not found**.
- Preserved the existing `WAFD Client Portal User` role check and project-level access isolation.
- Added website/cache refresh during migration so the corrected route is recognized immediately after deploy.

## No business-data changes
- No projects, contracts, inventory, invoices, payments, delivery records, or client mappings are modified.
- Existing RC169 `WAFD Client Portal Access` records remain valid.

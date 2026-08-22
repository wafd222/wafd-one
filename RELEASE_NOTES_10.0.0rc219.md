# WAFD ONE 10.0.0 RC219

## Mobile navigation root-cause fix

- Fixed the global mobile back control using the active Frappe route as the source of truth.
- Removed the incorrect DOM-only home detection that treated hidden cached SPA pages as the current page.
- The WAFD ONE role home remains free of a back button.
- Internal hub pages such as Operations, Finance, Inventory, Delivery, Documents, and Undertaking screens now receive the mobile back control.
- Added a visible-page fallback only for the short period before the Frappe router is ready.
- Replaced the back-control ID with `wafd-mobile-back-v219` and removes RC218/legacy controls to avoid stale collisions.
- No changes to undertaking templates, PDF generation, permissions, signature, stamp, or business workflow.

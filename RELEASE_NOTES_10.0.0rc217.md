# WAFD ONE 10.0.0 RC217

## Frappe SPA Home Back-Control Lifecycle Fix

- Fixes the persistent blank mobile back-control square on the WAFD ONE role home page.
- Initialises the global navigation MutationObserver correctly even when app JavaScript loads after DOMContentLoaded.
- Treats both `.wafd-role-home` and the Frappe page wrapper `.wafd-role-home-page` as authoritative home-page markers.
- Adds direct cleanup in role-home `on_page_load` and `on_page_show` as a second safety layer.
- Keeps the back control limited to internal pages only.
- No changes to undertaking workflow, PDF generation, permissions, signature, stamp, or terms.

# WAFD ONE 10.0.0 RC381

## Scope
Fix repeated-entry and final-report click failures in the external Iftar monitoring screen on mobile Safari/Frappe cached pages.

## Changes
- Delegate role-home card clicks from the document so they survive a detached/recreated Frappe page-body node.
- Delegate the final-report stage action from the viewer root instead of binding only to individual rendered stage elements.
- Add the Frappe `on_page_show` lifecycle handler to reconnect the live viewer root, clear a stale report-return freeze, and reload the current date on subsequent visits.
- Preserve the current report popup workflow, approval gates, roles, permissions, business rules, and stored data.

## Validation
- JavaScript syntax checks and focused regression tests are required before release.
- Live iPhone/Frappe Cloud validation remains required; this ZIP cannot establish production behavior by itself.

## Explicitly unchanged
No unrelated modules, workflow stages, permissions, pricing, inventory, or operational data were changed.

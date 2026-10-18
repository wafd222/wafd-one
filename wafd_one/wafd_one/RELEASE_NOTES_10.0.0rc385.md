# WAFD ONE 10.0.0 RC385 — External Authority Viewer Route Guard Repair

## Root cause reproduced

The globally injected `wafd_mobile_navigation.bundle.js` includes `WAFD Iftar Authority Viewer` in its field-only role set, but omits the viewer's own `wafd-iftar-authority-viewer` page from `fieldRouteIsAllowed()`. Every Frappe route change and DOM observer render can call `enforceFieldHome()` and silently route the external viewer back to `wafd-role-home`. The report return and re-entry expose this conflict. Earlier RC381–RC384 card/report changes did not change this guard.

## Narrow fix

- Allow `wafd-iftar-authority-viewer` through the global field route guard **only** for users assigned `WAFD Iftar Authority Viewer`.
- Apply the same correction to both the loaded `public/wafd_mobile_navigation.bundle.js` and maintained `public/js/wafd_mobile_navigation.js`.
- Keep all other field routes, report rendering, role-home card, project logic, and backend permissions unchanged.
- Bump release metadata to RC385.

## Verification

- Before the patch, an executable Node.js simulation of the actual RC384 bundle reproduced a silent redirect from the authority viewer to role home.
- After the patch, repeat authority viewer → home → authority viewer five times under both standard and `Page` Frappe route shapes without redirects.
- Verify unauthorized field roles still redirect from the authority viewer, and authority viewers still redirect from site management.
- Run Python test suite, JavaScript syntax checks, and ZIP integrity checks.

**Limit:** No live Frappe Cloud/iPhone browser validation. After deployment, ensure the new `wafd_mobile_navigation.bundle.js` is built and served (not cached) before testing.

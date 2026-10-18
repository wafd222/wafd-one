# WAFD ONE RC388 — External Iftar viewer mobile header/layout root fix

## Cause and fix
The global WAFD field appbar was prepended to the Frappe `.page-container`. In mobile Frappe layouts that container can be a flex row, so the appbar and viewer content competed for the same row, each occupying roughly half the viewport. Viewer-local CSS in RC386–RC387 cannot repair a sibling inserted *inside* the page's parent layout.

For **only** `wafd-iftar-authority-viewer`, the global navigation controller now mounts its existing appbar as a direct child of `document.body` instead of as a sibling of the page content. Other WAFD routes keep their existing appbar placement. When switching away, the original placement is restored.

- RC385 route guard and return behavior unchanged.
- Final report stage and RC386 redundant-share-button removal unchanged.
- No server-side permission, data model, operational workflow or other role change.
- Simulated real DOM layout in Chromium and checked restoration on route changes; iPhone/Safari live verification remains pending.

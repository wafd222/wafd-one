# WAFD ONE RC389 — Isolated External Iftar Viewer Mobile Surface

The external Iftar authority viewer no longer overrides the visibility/display of cached Frappe Page wrappers. RC387 had forced `display:block !important` on the Page wrapper, potentially defeating Frappe's hide/show lifecycle and leaving stale page columns visible. RC388 changed a field appbar branch that was not active on this viewer route. Those changes are replaced by a dedicated mobile-only viewport attached directly to `document.body`, with a compact WAFD ONE header and Home/Logout menu. On route changes the viewport is hidden; the original viewer root and report handlers are retained and re-used. Desktop keeps the regular Frappe page layout. No changes to backend roles, assignments, business operations, or report content.

Browser tests cover a simulated 50/50 parent shell, mobile 390/430/768px layouts, navigation away/back, and desktop view. Live Safari verification pending.

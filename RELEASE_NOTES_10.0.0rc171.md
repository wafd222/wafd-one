# WAFD ONE 10.0.0 RC171

## Client portal website API fix
- Replaces Desk-only `frappe.call` usage on `/wafd-client` with same-origin REST `fetch` calls, so Website Users can load their assigned projects.
- Removes remaining Desk-only `frappe.msgprint` / `frappe.show_alert` dependencies from the external portal.
- Keeps RC170 route fix, role checks and per-user/per-project isolation unchanged.
- Uses the logged-in session cookie for read calls and `window.csrf_token` for the receipt confirmation POST.
- Uses local browser date rather than UTC for the default service date.

No inventory, finance, project, permission mapping or internal Desk workflow data is modified by this release.

# WAFD ONE 10.0.0rc373 — Iftar Viewer Page Permission Repair

- Adds a narrowly scoped post-migration repair for the `wafd-role-home` and `wafd-iftar-authority-viewer` Page role rows. This addresses upgraded sites where stale database Page permissions can block the route before the viewer JavaScript runs and show Frappe's generic `Not permitted` dialog.
- The repair adds only missing role rows to those two pages, preserves all existing role rows, and clears the Page/cache state only when it makes a change.
- Keeps the external viewer's project assignment and read-only data scope unchanged. Does not modify hotel delivery records, normal delivery viewer permissions, or unrelated modules.
- Retains the RC372 final-report fallback and mobile navigation fix.

Validation: Python compilation; 30 focused Iftar workflow and pricing tests; JavaScript syntax checks. Live Frappe Cloud deployment and account acceptance testing are still required to confirm the permission repair against the site's actual Page records.

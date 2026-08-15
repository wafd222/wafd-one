# WAFD ONE 10.0.0 RC160

## Frappe v16 navigation / Production Batch visibility

- Added a standard app-level `Workspace Sidebar` for WAFD ONE, which is the supported navigation model in Frappe v16.
- Added an explicit `دفعات الإنتاج / WAFD Production Batch` navigation item routed through the role-restricted Production Batch Page.
- Preserved the existing Production Supervisor Production Batch permissions.
- Expanded the redirect Page roles to all WAFD roles that already have legitimate read access to Production Batch.
- Repairs stale per-user WAFD ONE sidebar copies for users with the Production Supervisor role so an old private sidebar cannot shadow the corrected standard sidebar.
- Clears navigation/permission cache after migration.
- No operational records or completed projects are changed.

## Root cause

Frappe v16 changed Desk navigation to `Workspace Sidebar`. Without a standard curated sidebar, Frappe auto-generates a module sidebar and limits DocType entries; therefore `WAFD Production Batch` was absent from Ctrl+K/navigation even while its DocType permissions were correct.

# WAFD ONE 10.0.0rc162

## Frappe v16 migration recovery

- Fixes the RC161 migration failure `KeyError: name` while syncing the app-level `Workspace Sidebar`.
- Adds the mandatory document `name` (`WAFD ONE`) to `wafd_one/workspace_sidebar/wafd_one.json`.
- Preserves the RC161 migration-safe navigation repair and Production Batch permission matrix.
- No operational projects, invoices, stock movements, or historical records are modified by this release.

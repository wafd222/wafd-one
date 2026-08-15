# WAFD ONE 10.0.0rc159

## Production Batch visibility fix

This release is intentionally limited to the Production Supervisor navigation defect confirmed after RC158.

- Makes `WAFD Production Supervisor` Read / Write / Create / Select / Print / Report access explicit in both standard metadata and the deployed-site Custom DocPerm matrix.
- Adds explicit Production Batch search fields for normal list/link discovery.
- Adds a role-restricted Desk route titled `WAFD Production Batch`; selecting it from Ctrl+K redirects to the real `WAFD Production Batch` List view.
- Renders the already-defined `دفعات الإنتاج` shortcut in the visible WAFD ONE workspace immediately after Daily Meal Plans.
- Normalizes the Frappe Role `search_bar` flag when that schema field exists.
- Rebuilds WAFD ONE workspace metadata and clears Desk/permission caches during migration.
- Preserves RC158 restricted-page visibility rules.
- Does not modify projects, production records, invoices, payments, or completed operational data.

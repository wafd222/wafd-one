# WAFD ONE 10.0.0 RC112 — Migration Compatibility Fix

- Fixed the RC111 migration failure on Frappe v16 / Python 3.14.
- Removed the unsupported `ignore_permissions` argument from `frappe.rename_doc`.
- The failed RC111 patch can now rerun safely and rename malformed Iftar project IDs while updating linked records.
- No business data, project records, or Iftar workflow features were removed.

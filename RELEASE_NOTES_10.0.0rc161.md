# WAFD ONE 10.0.0rc161

## Migration recovery + Frappe v16 Production Batch navigation

- Removes the RC160 `wafd_one.patches.v10_0_0_rc160.execute` entry that caused Frappe Cloud migration to fail with `ModuleNotFoundError: No module named 'wafd_one.patches'` on the deployed checkout.
- Moves the RC160 navigation repair into the already-existing `wafd_one.setup.after_migrate` hook, avoiding any dependency on a newly-added nested patch package.
- Keeps migration resilient: navigation repair errors are logged instead of aborting schema migration.
- Reasserts the exact least-privilege `WAFD Production Batch` permission matrix.
- Rebuilds the standard Frappe v16 `WAFD ONE` Workspace Sidebar with a direct DocType link to `WAFD Production Batch` (no intermediary Page required).
- Refreshes stale private WAFD ONE sidebar copies for Production Supervisor users.
- Ensures the WAFD ONE landing workspace contains the `دفعات الإنتاج` shortcut and visible content block.
- Does not alter projects, production records, invoices, payments, stock transactions, or completed operational data.

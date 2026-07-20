# WAFD ONE v6.0.4

## Migration safety hotfix

- Removes unsafe duplicate `frappe.reload_doc` calls from the v6.0.0 and v6.0.1 governance patches.
- Preserves the published patch paths so partially migrated sites can resume safely.
- Initializes governance defaults only after confirming the DocType exists.
- Adds valid `creation` and `modified` timestamps to seven metadata JSON files that previously had empty or missing values.
- Prevents the Frappe import comparison error between `NoneType` and `datetime.datetime`.
- Keeps both patches idempotent and safe to retry.

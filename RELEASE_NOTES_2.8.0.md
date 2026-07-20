# WAFD ONE 2.8.0

- Rebuilds the public WAFD ONE Workspace directly in the site database.
- Removes stale/incomplete Workspace child rows before recreating them.
- Persists and validates all seven Phase 1 shortcut records and content blocks.
- Adds the Frappe v16 `app` and `type` Workspace fields.
- Clears user/workspace caches after migration.
- Uses a database savepoint and rolls back safely if validation fails.

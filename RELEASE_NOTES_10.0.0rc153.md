# WAFD ONE 10.0.0 RC153

## Permissions finalization
- Fixes Desk login for all WAFD operational roles, including Storekeeper.
- Normalizes `Role.desk_access = 1` for existing roles, not only newly-created roles.
- Keeps the RC152 least-privilege DocType permission matrix unchanged.
- Clears permission/session metadata cache after migration.

This addresses the acceptance-test failure where a correctly assigned WAFD Storekeeper received the Frappe message that no role was allowed to access Desk.

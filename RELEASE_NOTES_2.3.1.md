# WAFD ONE 2.3.1

## Migration hotfix

- Removed the `v2_3.rebuild_workspace_and_phase_one` pre-model-sync patch that attempted to insert the Workspace before its linked DocTypes were synchronized.
- Workspace setup now checks that every referenced WAFD DocType exists before insertion.
- Workspace rebuilding remains in the `after_migrate` hook, where the schema and DocTypes are already available.
- This resolves `frappe.exceptions.LinkValidationError: Could not find Link To: WAFD Mission / WAFD Hotel / WAFD Contract / WAFD Meal Plan ...` during site migration.

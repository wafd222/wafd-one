# WAFD ONE 10.0.0 RC313

## Iftar participant name entry fix

This release fixes only the restored Iftar Saim daily receipt dialog discovered during RC312 testing.

### Fixed
- `اسم صاحب السفرة` is now a normal text entry field, so a new name can be entered even when no roster was pre-created.
- `اسم المشرف` is now a normal text entry field for the same reason.
- `مدير المشرفين` and assistant names also accept manual entry to prevent the same empty-list problem later in the workflow.
- Previously entered Iftar table-owner, supervisor, manager and assistant names are added to the reusable project roster automatically for later operating days.
- Existing saved names remain visible as hints; no existing Iftar records are deleted or changed.

### Scope protection
- No changes to Delivery Management, Delivery Supervisor, driver, offline sync, trips, schedules or delivery reports.
- No changes to Undertaking, Quotation, Inventory, Cleaning, Finance, users or languages.
- The RC313 migration only clears cache; it does not reload or mutate unrelated DocTypes.

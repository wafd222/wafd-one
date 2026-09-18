# WAFD ONE 10.0.0 RC319

## Iftar delivery-supervisor task visibility and duplicate-entry fix

- Treat the explicit Iftar project assignment as the authoritative source for project/task visibility.
- An assigned Delivery Supervisor now sees the project even if the User-role cache is stale after assignment.
- Keep exact-user assignment security: unassigned users do not gain access to the project.
- Remove the legacy/manual Iftar-delivery entry button from the Delivery Supervisor delivery-management screen to avoid two competing Iftar workflows.
- Keep the legacy/manual Iftar-delivery creator available to System Manager and WAFD Operations Manager only.
- Preserve the RC317/RC318 driver offline capture and reconnect synchronization fixes.
- No changes to driver trip logic, offline queue, Undertaking, Quotation, Inventory, Cleaning, Finance, or other unrelated modules.

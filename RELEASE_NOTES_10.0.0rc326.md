# WAFD ONE 10.0.0 RC326

## Iftar supervisor setup and task creation fix
- Fixes the Frappe v16 child-table permission error raised while Site Manager saves supervisors/table owners.
- Treats `WAFD Iftar Distribution Recipient` only as a child of the Iftar Project during trusted project-scoped synchronization.
- Saves Supervisor Plans with project-scoped elevated write context after explicit assignment/role validation.
- Generates today's supervisor daily reports server-side in the same operation when authority inspection is approved.
- Removes the duplicate client-side second task-generation call.
- Preserves all RC320 driver/offline and standard delivery behavior unchanged.

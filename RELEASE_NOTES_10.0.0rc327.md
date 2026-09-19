# WAFD ONE 10.0.0 RC327

## Iftar supervisor/table-owner permission fix
- Fixes the remaining `WAFD Iftar Distribution Recipient` permission error when saving supervisor/table-owner setup.
- Stops re-saving the whole Iftar Project from the Supervisor Plan hook.
- Rebuilds only the project's `distribution_recipients` child rows directly as child records with the correct parent, parenttype and parentfield.
- Keeps the legacy carton/distribution workflow synchronized without granting standalone permissions to the child DocType.
- Preserves RC326 quick supervisor setup and automatic daily task creation.
- No changes to driver/offline, standard delivery, Undertaking, Quotation, Inventory, Cleaning, Finance, or unrelated modules.

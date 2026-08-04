# WAFD ONE 10.0.0rc21

## UAT inventory preparation

- Adds an explicit **Prepare UAT Test Stock** action to Planned production batches.
- Creates auditable, posted WAFD receipt movements only for the current batch shortages.
- Uses ingredient category-to-warehouse mapping and adds missing source warehouses safely.
- Adds a configurable test buffer (default 25%).
- Requires System Manager, WAFD Operations Manager, or WAFD Storekeeper.
- Never runs automatically during migration and never alters existing positive stock.
- Every generated movement is labelled `UAT TEST STOCK ONLY`.

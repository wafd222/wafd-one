# WAFD ONE 10.0.0rc11

- Recalculate live available stock as actual quantity minus reserved quantity.
- Normalize legacy WAFD Stock Balance rows during migration.
- Repair production batches missing source-warehouse child rows.
- Add Stock Diagnostics action to distinguish missing stock records from true zero balance.
- Auto-calculate packaging box count when units per box is configured.
- Preserve all existing quality, food-safety, loading, delivery, invoicing, and payment gates.

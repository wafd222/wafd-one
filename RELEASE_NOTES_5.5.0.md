# WAFD ONE v5.5.0 — Procurement and Inventory Control

- Added purchase-order-driven goods receipt creation.
- Supports partial receipts while preventing over-receipt.
- Automatically synchronizes received quantities and purchase order status from posted stock receipts.
- Locks posted stock movements against editing and deletion.
- Validates ingredient activity, UOM consistency, warehouse matching, dates, quantities, and costs.
- Prevents duplicate ingredients within purchase orders and stock movements.
- Protects purchase orders with posted receipts from cancellation or deletion.
- Strengthened stock-balance nonnegative quantity, reservation, cost, and UOM controls.
- Added a migration patch to rebuild purchase-order receipt totals safely.

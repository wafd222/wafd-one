# WAFD ONE 10.0.0 RC318

## Driver reconnect synchronization conflict fix

- Fixes Frappe `modified after you have opened it` errors while replaying driver actions saved offline.
- Serializes offline replay per delivery trip with a database row lock.
- Uses field-level database updates for driver arrival transitions so dashboard/realtime refreshes cannot invalidate a stale document object.
- Keeps start/arrival/proof replay idempotent; already-synced actions remain safe to retry.
- Preserves the original offline capture time and all queued proof data.
- No changes to Iftar, Delivery Supervisor, management delivery screens, Undertaking, Quotation, Inventory, Cleaning, or Finance.

# WAFD ONE 10.0.0 RC316

## Migration packaging fix

- Fix RC315 Frappe Cloud migration import by packaging `v10_0_0_rc315` as a proper patch package containing `execute.py` and `__init__.py`.
- Keep the RC315 patch path unchanged in `patches.txt`, so a failed RC315 migration can be retried safely after updating to RC316.
- No operational workflow, Delivery Management, driver, trip, offline, Undertaking, Quotation, Inventory, Finance, or Iftar business logic changes.
- Align package version metadata to 10.0.0rc316.

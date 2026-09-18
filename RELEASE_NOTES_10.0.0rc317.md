# WAFD ONE 10.0.0 RC317

## Driver offline reliability hotfix

- Driver actions now test real server reachability instead of relying only on `navigator.onLine`.
- Start, arrival, and delivery proof are written to IndexedDB immediately when Frappe Cloud is unreachable.
- Delivery photos, signature, quantities, receiver details, notes, GPS and device timestamp remain queued on the phone and replay in order after reconnect.
- Driver connectivity notices are suppressed on the driver page even when the account has additional WAFD roles.
- GPS acquisition is awaited before validating a simple delivery proof.
- Delivery images are compressed more conservatively for reliable mobile offline storage.
- Existing RC293/RC308 offline database and queued actions remain compatible.
- No business logic changes outside the driver offline page/guard.

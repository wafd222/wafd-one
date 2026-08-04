# WAFD ONE 10.0.0 RC60

- Simulates the entire contract stock rollback newest-first before deletion or reset.
- Automatically resolves stock dependencies that belong to the same test contract, without manual intervention.
- Blocks only when stock was consumed or reserved by records outside the cleanup chain, or when a legacy Adjustment cannot be reconstructed safely.
- Shows the exact automatic quantity changes per item and warehouse before execution.
- Returns a clear completion report describing reversed movements and restored/removed quantities.
- Keeps the whole cleanup transactional: any failure rolls back every change.

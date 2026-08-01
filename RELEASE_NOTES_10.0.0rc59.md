# WAFD ONE 10.0.0 RC59

- Adds a non-mutating stock reversal preflight before contract reset or permanent deletion.
- Shows exact blocked ingredient, warehouse, required quantity, current quantity, reserved quantity, and likely later stock movements.
- Disables destructive actions when stock cannot be restored safely.
- Re-runs the preflight on the server immediately before deletion to prevent race conditions and partial cleanup.
- Preserves transactional rollback: no contract links or records are changed when preflight fails.
- Keeps DELETE/RESET confirmation workflow and safe stock reversal from RC58.

# WAFD ONE 10.0.0rc29 — Production Stability Review

## Implemented
- Changed `WAFD Audit Event.reference_name` from Dynamic Link to immutable textual Data. Audit history remains intact but no longer blocks deletion of the referenced document.
- Kept audit events immutable and non-deletable for governance integrity.
- Changed production deadline handling from a hard validation error to `متأخر / Delayed`. The actual completion can be recorded and the workflow can continue.
- Added a clear orange completion warning when production ends after the service deadline.
- Added migration patch `v10_0_0_rc29` for deterministic metadata repair on existing sites.

## Safety policy
Posted stock movements remain protected and cannot be deleted. This is intentional accounting and inventory control. Draft production batches with only audit history can now be deleted normally after migration.

# WAFD ONE 10.0.0rc22

## Production-readiness hardening

- Corrected DocType synchronization order during install and migration.
- Child-table DocTypes are now loaded before parent DocTypes that reference them.
- Dependency order is derived directly from the shipped DocType JSON metadata.
- Added deterministic defensive handling for unexpected circular metadata references.
- Revalidated Python syntax, JSON metadata, patch paths, release version, role definitions, JS server methods, Link targets and child-table targets.

This release does not add new operational complexity. It hardens installation and migration reliability before the final end-to-end workflow test.

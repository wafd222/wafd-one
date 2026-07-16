# WAFD ONE v2.6.0

- Removed active references to obsolete migration patches.
- Restored the historical `apply_setup` compatibility entry point.
- Added one idempotent post-model-sync repair patch.
- Explicitly reloads all 28 WAFD ONE DocTypes in dependency-aware order.
- Reloads the Workspace only after all seven linked DocTypes exist.
- Keeps role creation before migration and access setup after migration.

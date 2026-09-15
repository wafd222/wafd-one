## Summary

- Routed storekeeper-only users directly to the practical Storekeeper workspace, removing the duplicate role-home step without changing manager access.
- Simplified purchase receipt so the selected warehouse immediately loads its matching materials; packaging warehouse selection now shows packaging items directly.
- Fixed mobile material-card overflow and horizontal shifting with constrained responsive layouts and vertical-only result scrolling.
- Split the delivery supervisor board into four mutually exclusive operational queues: In Transit, Planned, Late/Undocumented, and Delivered.
- Added queue counts, time-based sorting and clear visual status accents while preserving edit/archive actions and the delivery log.
- Made meals, Safandash and Hot Cabinet counts visible on every delivery card, including zero values.
- Added an idempotent RC296 page-refresh patch and focused static validation.

## Validation

- `python scripts/validate_storekeeper_delivery_rc296.py`
- `python scripts/validate_material_catalog_rc295.py`
- `python scripts/validate_practical_storekeeper_rc268.py`
- `python scripts/validate_storekeeper_experience.py`
- `python scripts/validate_patch_paths.py`
- `python scripts/validate_release.py`
- Python compile, JavaScript syntax and DocType JSON validation passed.

## Summary

- Removed the duplicated top delivery-status summary from the Delivery Supervisor page and kept the lower interactive queue cards as the single control set.
- Added the same In Transit, Planned, Late/Undocumented and Delivered filters to the read-only Delivery Data page.
- Unified server-side delivery bucketing and queue counts across supervisor and viewer screens.
- Kept meal, Safandash and Hot Cabinet quantities optional in supervisor delivery forms.
- Rendered optional quantity cards only when the supervisor entered a positive value; blank and zero values remain hidden in Delivery Data.
- Preserved read-only viewer permissions, delivery proof, timeline, driver and vehicle information.
- Added an idempotent RC297 page-refresh patch and focused validation.

## Validation

- `python scripts/validate_delivery_viewer_filters_rc297.py`
- `python scripts/validate_storekeeper_delivery_rc296.py`
- `python scripts/validate_patch_paths.py`
- `python scripts/validate_release.py`
- Python and JavaScript syntax validation passed.

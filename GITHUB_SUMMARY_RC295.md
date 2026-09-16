## Summary

- Added a curated catalogue of 560 catering, food, packaging, cleaning, serving and kitchen-equipment materials across 22 operational sections.
- Corrected legacy misclassifications such as fruits under vegetables, poultry under meat, dairy/sugar under beverages, and cleaning supplies under generic materials.
- Added dedicated Flour & Milling, Dates & Nuts, Packaged Foods, Frozen Foods & Pastries, Utensils & Equipment, and Serving Supplies sections.
- Scoped receipt and handover category selectors to the selected warehouse or cold room, increased searchable results to 600, and prevented receipts into an incompatible warehouse.
- Added an idempotent RC295 migration that preserves document names, item codes, prices, suppliers, balances and posted stock movements.
- Added RC295 catalogue integrity, legacy coverage, UI and patch-path validation.

## Validation

- `python scripts/validate_material_catalog_rc295.py`
- `python scripts/validate_practical_storekeeper_rc268.py`
- `python scripts/validate_storekeeper_experience.py`
- `python scripts/validate_patch_paths.py`
- `python scripts/validate_release.py`
- Python compile, JavaScript syntax and DocType JSON validation passed.


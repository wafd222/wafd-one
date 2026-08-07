# WAFD ONE 10.0.0rc132

## Migration hotfix

- Added the missing Python controller module for the child DocType `WAFD Iftar Daily Photo`.
- Fixes Frappe migration failure during DocType sync:
  `ModuleNotFoundError: wafd_one.wafd_one.doctype.wafd_iftar_daily_photo.wafd_iftar_daily_photo`.
- No schema or workflow behavior was changed; the fix only restores the required Frappe DocType module contract so migration can complete safely.

## Validation

- All DocType folders now contain their expected Python controller module.
- Python syntax compilation passed.
- JSON parsing passed.
- Existing release validation and patch-path validation passed.

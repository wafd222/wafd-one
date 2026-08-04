# WAFD ONE v7.6.1

## Migration hotfix

- Restored the missing Python controller module for `WAFD Procurement Plan Item`.
- Fixes `ModuleNotFoundError` during Frappe `Migrate Site`.
- Verified all exported DocTypes have matching importable controller modules.
- No database records are deleted or reset by this hotfix.

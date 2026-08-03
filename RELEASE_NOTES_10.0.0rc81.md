# WAFD ONE 10.0.0 RC81

## Migration hotfix

- Added the missing Python controller modules for the three child DocTypes introduced by the Iftar module:
  - WAFD Iftar Meal Item
  - WAFD Iftar Distribution Row
  - WAFD Iftar Hospitality Item
- Fixes `ModuleNotFoundError` during Frappe site migration.
- No operational data is deleted or replaced.

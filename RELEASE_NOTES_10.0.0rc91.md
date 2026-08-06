# WAFD ONE 10.0.0 RC91

## Migration correction

- Fixed the RC89 recipe migration failure caused by the unsupported `سحور / Suhoor` recipe category.
- Maps the Suhoor reference recipe to the supported `إفطار / Breakfast` category without changing operational meal-plan support for Suhoor elsewhere.
- Added runtime validation against the actual WAFD Recipe category options so future unsupported recipe categories are skipped and logged instead of stopping site migration.
- Retains all RC89 and RC90 dashboard, warehouse, master-data, and nationality-link corrections.

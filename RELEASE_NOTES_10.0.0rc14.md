# WAFD ONE 10.0.0rc14

- Expanded operational catalogue for mission, seasonal, buffet, coffee-break and institutional menus.
- Added more raw materials, beverages, bakery, PPE, cleaning and operational stock masters.
- Added packaging material catalogue and reusable packaging profiles.
- Packaging records can select a profile, calculate units per box and packaging cost automatically, and prepare label text.
- No opening stock quantities are fabricated; all new inventory masters start at zero until an approved count or stock movement is posted.

## Migration hotfix

- Added the missing Python controller for `WAFD Packaging Profile Item`.
- Fixes `ModuleNotFoundError` during `Migrate Site` while syncing the packaging child DocType.

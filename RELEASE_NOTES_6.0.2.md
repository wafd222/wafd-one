# WAFD ONE v6.0.2

## Migration hotfix

- Corrected patch module paths for v5.3.0 through v5.6.0.
- These migrations are single Python modules, so patches.txt now references the module itself rather than a non-existent nested `execute` module.
- Added structural validation for every entry in patches.txt.

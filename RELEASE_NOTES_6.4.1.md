# WAFD ONE v6.4.1

## Migration hotfix

- Corrected legacy patch module paths for v5.3.0 through v5.6.0.
- File-based patch modules are now referenced directly, while package-based patches continue to reference their execute module.
- Added full patch-path validation to prevent ModuleNotFoundError during Frappe migrations.
- Retains the v6.4.0 JSON metadata, Hotel Undertaking, and 400-hotel catalogue fixes.

# WAFD ONE 5.0.1

## Migration safety fix

- Replaced the unsupported `MultiSelect` database field for undertaking meals with a schema-safe `Small Text` field.
- Hardened the v5.0.0 migration patch so it verifies actual table columns before running updates.
- Preserved automatic meal defaults and one-meal-per-line editing.
- Prevented `Unknown column meal_types` from blocking Frappe Cloud migration.

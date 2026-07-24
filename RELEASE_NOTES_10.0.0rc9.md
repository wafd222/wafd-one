# WAFD ONE 10.0.0rc9

- Removes empty Source Warehouse child rows before validation.
- Automatically loads project or kitchen warehouse defaults into daily plans.
- Falls back safely to the first active WAFD Warehouse when no explicit default exists.
- Repairs blank source rows and missing warehouse defaults during migration.
- Keeps the source warehouse table authoritative while preserving backward compatibility.
- Prevents the mandatory child-row error seen when saving a correctly populated daily meal plan.

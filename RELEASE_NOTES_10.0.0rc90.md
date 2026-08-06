# WAFD ONE 10.0.0 RC90

## Migration reliability fix

- Resolves mission country links to the canonical bilingual `WAFD Nationality` record.
- Ensures the Indonesian nationality master exists before RC89 master-data loading.
- Repairs incomplete legacy mission nationality links idempotently.
- Prevents `LinkValidationError: Could not find Country-Nationality: إندونيسيا`.
- Retains all RC89 dashboard, warehouse, finance, recipe, and inventory improvements.

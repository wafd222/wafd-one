# WAFD ONE v5.4.0

## Costing and master-data stability

- Corrected ingredient price unit conversion against the ingredient base UOM.
- Added persisted latest market price fields to ingredients.
- Approved prices now update standard cost; benchmark prices remain informational.
- Added safe price refresh after update and deletion.
- Added strict recipe validation for yield, duplicate ingredients, quantities, inactive ingredients, and margin limits.
- Added hotel coordinate and verification-date validation.
- Added migration patch to refresh existing ingredient market costs.
- Completed Python, JSON, field-order, duplicate-field, and ZIP integrity checks.

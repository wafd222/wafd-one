# WAFD ONE 10.0.0rc27

## Recipe quantity mapping repair

- Standardized recipe output on `required_quantity` while retaining the legacy `quantity` alias.
- Production material calculations now read the canonical field safely.
- Added explicit validation for planned quantity, recipe yield, and invalid ingredient rows.
- Added direct recipe diagnostics so valid recipe quantities are no longer incorrectly reported as zero.
- Improved bilingual error details for invalid recipe rows and failed requirement mapping.

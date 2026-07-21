# WAFD ONE v6.3.0

- Fixed Hotel Undertaking preview and PDF export by removing the unsupported `frappe.get_single` call from Jinja print rendering.
- Rebuilt the undertaking layout for A4 output with high-resolution logo, signature, and stamp handling.
- Permanently disabled both full reset and reference-data deletion endpoints.
- Added a safe, idempotent directory of 400 Madinah accommodation properties sourced from OTA directories and existing WAFD references. Records are marked for licence verification and never overwrite user-entered fields.
- Added authoritative food-data source manifest for USDA FoodData Central, FAO/INFOODS, WHO, and WAFD operational recipes.

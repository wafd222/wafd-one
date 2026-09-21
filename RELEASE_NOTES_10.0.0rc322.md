# WAFD ONE 10.0.0 RC322

Packaging correction for RC321 deployment.

- Restores the root `pyproject.toml` required by Frappe Cloud validation.
- Restores standard package metadata files omitted from the RC321 ZIP.
- Keeps the complete RC321 application directory unchanged except version metadata.
- No business-logic changes to Iftar, delivery, driver offline, undertaking, quotation, inventory, finance, or other modules.

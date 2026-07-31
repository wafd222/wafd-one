# WAFD ONE 10.0.0rc47

## Fixed

- Prevented the shared **WAFD Project Service** child-table handler from writing contract-only totals to a **WAFD Catering Project** form.
- Resolved the browser error: `frm.set_value: services_subtotal does not exist in the form`.
- Kept contract service subtotal, VAT, grand total, advance, and outstanding calculations unchanged on the **WAFD Contract** form.

## Validation

- JavaScript syntax validation passed.
- Python compilation passed.
- Package version synchronized in `wafd_one/__init__.py` and `pyproject.toml`.

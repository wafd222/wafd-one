# WAFD ONE 4.8.8

## Migration compatibility fix

- Added the valid recipe category `وجبة خفيفة / Snack` to the standard `WAFD Recipe.meal_category` Select options.
- This matches the reference recipe `وجبة فواكه فردية` loaded by the historical `v4_6.load_reference_master_data` patch.
- Prevents Frappe Select-field validation from aborting Update Site Migrate and rolling the site back to the previous commit.
- Audited every Select value used by `master_data.py` against the corresponding DocType JSON options. No other mismatches were found.
- No operational records are deleted or overwritten.

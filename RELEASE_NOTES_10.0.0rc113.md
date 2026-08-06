# WAFD ONE 10.0.0 RC113

## Migration package compatibility fix

- Restores the importable package for `wafd_one.patches.v10_0_0_rc111.execute`.
- Makes empty Python package initializers non-empty so web/GitHub uploads do not omit them.
- Keeps the RC111 rename migration and the RC112 Frappe compatibility correction intact.
- Removes generated Python cache files from the release archive.

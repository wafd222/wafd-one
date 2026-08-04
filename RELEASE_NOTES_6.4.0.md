# WAFD ONE 6.4.0

Stability release that fixes Frappe v16 schema migration failures caused by missing or blank metadata timestamps in exported JSON files.

## Included
- Valid `creation` and `modified` timestamps for every synchronized DocType, Page, Workspace, Report and Print Format JSON document.
- Safe Hotel Undertaking print-format enforcement without server calls inside Jinja.
- Verified non-destructive installation of the 400-row Madinah hotel catalogue.
- Migration regression validation for metadata timestamps, patch modules, Python and JSON syntax.

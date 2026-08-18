# WAFD ONE 10.0.0 RC190

Final undertaking PDF reliability correction.

- Sanitizes every HTML image source before wkhtmltopdf; local assets/files are embedded as data URIs and unresolved/remote images are removed.
- Sanitizes CSS url(...) image references as well.
- Recovers legacy uploaded signature/stamp from either WAFD Print Settings or the active Document Studio template.
- Backfills existing undertakings and clears compiled undertaking templates during migrate.
- Replaces the large text Back control with a compact icon-only mobile navigation button.
- No workflow, finance, permissions, inventory, or approved undertaking layout changes.

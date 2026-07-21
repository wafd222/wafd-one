# WAFD ONE 6.3.4

Reviewed stability correction for the Hotel Undertaking repair and 400-hotel catalogue installer.

- Fixes missing module-level `json` and `Path` imports that could stop `after_migrate`.
- Restricts print-format repair strictly to WAFD Hotel Undertaking formats.
- Prevents unrelated print formats from being reassigned.
- Strengthens post-repair validation.
- Removes generated Python cache files from the release package.

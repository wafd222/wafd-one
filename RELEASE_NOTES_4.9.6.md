# WAFD ONE 4.9.6 — Full Migration Audit

- Replaced the ambiguous v4.8.1 and v4.8.2 compatibility imports with real callable patch functions.
- Kept v4.9.3 Select values aligned with the installed WAFD Hotel metadata.
- Removed explicit database commits from hotel import patches so Frappe controls migration transactions.
- Removed generated Python cache files from the release package.
- Revalidated Python syntax, JSON metadata, patch paths, Select values, CSV structure, and hotel reference data.

- Prevented accidental hotel merging when the source map repeats a central map number for different hotel names.

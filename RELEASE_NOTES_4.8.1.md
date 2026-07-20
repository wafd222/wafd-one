# WAFD ONE 4.8.1

## Repository synchronization correction

- Restores the complete `patches.txt` sequence that was missing from the GitHub main branch.
- Adds a fail-fast v4.8.1 patch that reloads and validates `WAFD Administration Console`.
- Rebuilds the main WAFD ONE workspace and verifies the administration shortcut target.
- Keeps the standard Single DocType route `/app/wafd-administration-console`.
- Clears Frappe caches after successful validation.

## Required repository checks after upload

- `wafd_one/__init__.py` must show `4.8.1`.
- `wafd_one/patches.txt` must include `wafd_one.patches.v4_8_1.execute`.
- `wafd_one/hooks.py` must retain the complete v4.8 hooks file.

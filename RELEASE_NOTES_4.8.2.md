# WAFD ONE 4.8.2

## Administration Console registration fix

- Uses `WAFD Administration Console` as the single canonical administration entry.
- Explicitly exports it as a standard, searchable, non-custom Single DocType.
- Removes the duplicate Page JavaScript hook from active migration setup.
- Adds a fail-fast migration patch that validates the DocType, permissions, and main Workspace shortcut.
- Aligns package and application versions at 4.8.2.

## Expected route

`/app/wafd-administration-console`

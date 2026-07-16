# WAFD ONE 2.9.0

## Frappe v16 Workspace fix

- Added a stable `id` to every Workspace content block.
- Added a new post-model-sync patch that rebuilds the Workspace from the packaged source.
- Added migration-time validation for block IDs and all seven Phase 1 shortcuts.
- Kept the existing deterministic delete/recreate workflow and cache clearing.

This fixes the case where headings and paragraphs appeared but shortcut tiles were not rendered in Frappe v16.

# WAFD ONE 2.2.2

## Workspace recovery release

- Force-syncs the standard WAFD ONE workspace during site migration.
- Rebuilds workspace links, shortcuts, cards and Arabic section layout.
- Keeps the workspace public, visible and assigned to the `wafd_one` app.
- Clears the workspace document cache after migration.
- Adds a one-time migration patch for sites that already installed earlier releases.

## Required deployment step

After deploying the new bench image, run the site update/migration for the target site. A bench-only deployment does not apply the workspace database patch.

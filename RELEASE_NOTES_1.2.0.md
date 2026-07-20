# WAFD ONE 1.2.0

## Main fix
- Added the Frappe v16 `add_to_apps_screen` hook so **WAFD ONE** appears on the Desktop and app switcher.
- Added a dedicated WAFD ONE logo and direct route to `/desk/wafd-one`.
- Enforced the WAFD ONE workspace as public and visible after installation and migration.

## Reliability
- Kept all existing operational DocTypes and permissions.
- Removed explicit database commits from setup hooks.
- Added cache refresh after install/migrate.
- Updated package and runtime version to 1.2.0.

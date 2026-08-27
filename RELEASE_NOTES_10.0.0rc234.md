# WAFD ONE 10.0.0 RC234

## Reliable iPhone PWA menu and viewport containment

- Fixes the installed iPhone home screen so the large Frappe navbar/sidebar is reliably replaced by the compact WAFD ONE application bar.
- Uses one route-aware runtime state for both hiding Frappe chrome and showing the WAFD menu, preventing an iOS cold-launch asset-order race.
- Keeps only the essential standalone application actions:
  - Home
  - Language selection
  - Current account/user identity
  - Logout
- Moves the standalone language selector into the compact menu while preserving the existing selector in normal browser mode.
- Adds direct late-mounted Frappe sidebar/navbar handling and restores their previous display state immediately outside role home.
- Removes the negative mobile hero margin that widened the document beyond the iPhone visual viewport.
- Constrains the role-home page, hero, card grid and cards to the viewport and prevents horizontal overflow/edge artifacts.
- Preserves desktop behavior, browser-mode navigation, RC219 back navigation and all role permissions.
- No schema changes and no migration patch.
- No changes to undertakings, hotels, finance, inventory, delivery or other operational workflows.

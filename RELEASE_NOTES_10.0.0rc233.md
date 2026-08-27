# WAFD ONE 10.0.0 RC233

## Installed iPhone PWA navigation
- Replaces the Frappe Desk navbar/sidebar on the installed WAFD ONE role-home screen with a compact WAFD application bar.
- The compact menu preserves the essential actions requested for mobile:
  - Home
  - Language access
  - Current account/user identity
  - Logout
- Uses both CSS scoping and a route-aware JavaScript fallback because Frappe can mount/repaint the Desk navbar after page load on iOS.
- Frappe navbar state is restored immediately when navigating away from WAFD role home, so forms, lists and operational pages retain their normal controls.
- The custom application bar is hidden on Safari/browser mode and desktop, and appears only on installed standalone mobile WAFD role home.
- Preserves RC219 route-aware back navigation on non-home pages.
- No schema changes and no migration patch.
- No changes to undertakings, hotels, permissions, finance, inventory, delivery or other operational workflows.

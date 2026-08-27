# WAFD ONE 10.0.0 RC235

## Frappe v16 duplicate mobile header fix

- Fixes the two-header issue visible on the installed iPhone role-home screen after RC234.
- Hides Frappe v16's page-head/mobile header variants as well as the legacy navbar variants while the compact WAFD ONE PWA home shell is active.
- Applies the same deterministic late-mounted-element handling to the additional v16 header selectors.
- Restores every hidden Frappe header to its previous display state immediately when leaving role home.
- Keeps the approved compact WAFD ONE menu with Home, language, current user and Logout.
- Preserves the RC234 iPhone viewport containment and horizontal-overflow fix.
- No schema changes and no migration patch.
- No changes to undertakings, hotels, roles, permissions or operational workflows.

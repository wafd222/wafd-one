# WAFD ONE 10.0.0 RC216

## Mobile back control final rendering correction

- Never renders the floating back control on the actual WAFD role home page.
- Detects the mounted `.wafd-role-home` DOM in addition to URL/Frappe route state.
- Replaces the arrow glyph with a CSS-border-drawn child element for deterministic iOS Safari rendering.
- Removes duplicate/stale back controls and re-evaluates when Frappe mounts page content.
- No changes to undertaking business logic, permissions, PDF, signature, stamp, or terms.

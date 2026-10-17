# WAFD ONE 10.0.0 RC380

## Scope
Fix only the mobile role-home navigation issue where the “متابعة إفطار صائم” card becomes unresponsive after returning from the official report/PDF viewer.

## Changes
- Use delegated click handling for mobile role-home cards so refreshed/restored card elements remain clickable.
- Clear stale Frappe freeze overlays and pointer-event locks when the role home is shown again, and on iOS page-show/focus/visibility restoration.
- Keep all other modules, roles, operational stages, data, and business rules unchanged.

## Validation
- JavaScript syntax check passed.
- Regression checks confirm delegated card handling and role-home recovery hooks are present.
- Must verify on deployed Frappe Cloud/iPhone after installing the release.

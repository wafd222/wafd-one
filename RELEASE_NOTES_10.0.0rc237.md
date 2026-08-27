# WAFD ONE 10.0.0 RC237

## Saudi mobile validation and employee navigation fix

- Accepts Saudi mobile numbers in local `05xxxxxxxx`, `9665xxxxxxxx`, `+9665xxxxxxxx` and `009665xxxxxxxx` formats.
- Normalizes Saudi local numbers to the international E.164 format `+9665xxxxxxxx` before creating the User and Driver records.
- Accepts Arabic and Persian numerals and removes common spaces, hyphens and parentheses.
- Shows a clear Arabic validation message for invalid mobile numbers instead of the generic Frappe phone error.
- Replaces the floating employee-page back control with a reserved inline control that cannot cover form fields, filters, badges or buttons while scrolling.
- Redirects the legacy Undertaking Team page to the unified Employee Management page for managers.
- Preserves employee permissions, operational history and all RC236 account/task controls.

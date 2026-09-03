## WAFD ONE 10.0.0 RC259 — Existing Driver Shortcut Launch Repair

RC259 fixes the remaining driver launch failure by adding the missing Frappe website template behind the existing `/wafd-mobile` installed-app shortcut. The route can now resolve and execute its role-aware redirect, sending authenticated drivers directly to `/app/wafd-role-home` while preserving the login return path for signed-out users. A browser fallback redirect is included, and all RC258 bilingual quotation features remain unchanged.

# WAFD ONE 10.0.0 RC259

## Existing driver shortcut launch repair

- Adds the missing Frappe website template for the existing `/wafd-mobile` PWA shortcut.
- Allows Frappe to resolve the shortcut before executing the role-aware server redirect.
- Sends authenticated drivers directly to `/app/wafd-role-home`.
- Keeps the login return path for signed-out users.
- Includes an immediate browser fallback redirect if server-side routing is bypassed.
- Preserves all RC258 bilingual quotation, preview, PDF and workflow changes.

## Deployment

Deploy the application, run the site migration, clear the site cache and fully close then reopen the installed WAFD ONE app.

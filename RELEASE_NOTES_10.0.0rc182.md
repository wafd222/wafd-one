# WAFD ONE 10.0.0 RC182

- Corrects the RC181 routing regression for Frappe v16: Desk routes use `/desk`, not `/app`.
- Sets `app_home`, Apps screen route, PWA manifest `id`/`start_url`, and `/wafd-mobile` redirect to `/desk/wafd-role-home`.
- Adds a compatibility route for the RC181 path `/app/wafd-role-home` so previously installed mobile shortcuts are redirected through `/wafd-mobile` to the correct Desk page instead of showing Page not found.
- Keeps the RC181 mobile card alignment correction unchanged.
- No workflow, permission, finance, inventory, or operational logic changes.

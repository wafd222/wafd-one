# WAFD ONE 4.8.0

## Administration Console rebuilt on standard Frappe metadata

- Added **WAFD Administration Console** as a standard Single DocType, so access no longer depends on a custom Page or a separately visible Workspace.
- Added permissions for Administrator, System Manager, and WAFD Operations Manager.
- Added a permanent shortcut and link inside the main WAFD ONE Workspace.
- Added a dashboard entry for System Manager and WAFD Operations Manager users.
- Kept server-side permission enforcement and the exact destructive-action confirmation phrase.
- Added a migration patch that reloads the DocType and deterministically rebuilds the main Workspace.
- Fixed the administration dashboard card click handler so it cannot be intercepted by the generic DocType-card handler.
- Preserved the former administration Page only as a compatibility route.

# WAFD ONE 10.0.0 RC249

## Direct driver and employee home routing

- Opens the WAFD ONE role home directly after sign-in instead of showing the
  Page Not Found, Apps and Workspace screens first.
- Uses the canonical Frappe v16 Page route: `/app/wafd-role-home`.
- Removes the website route rule that incorrectly captured that Desk Page URL.
- Keeps `/wafd-mobile` as the role-aware PWA entry point for iPhone and Android.
- Redirects old `/desk/wafd-role-home` bookmarks to the canonical route.
- Repairs already-persisted WAFD ONE Desktop Icon links during migration.
- Preserves the separate client portal route and all employee role permissions.

## Deployment

Deploy the release and run the normal site migration. Confirm that Installed
Applications shows `10.0.0rc249`, then clear the site cache and sign out/in once.

# WAFD ONE 10.0.0rc158

## Permissions visibility repair

This release is intentionally limited to the role/Desk visibility defects confirmed during the RC157 Production Supervisor smoke test.

- Forces `WAFD Production Batch` metadata and permissions to synchronize on deployed sites.
- Grants `WAFD Production Supervisor` the required Read / Write / Create / Select / Print / Report access to Production Batch.
- Keeps Quality Inspector, Project Manager and Delivery Supervisor read-only on Production Batch.
- Removes stale manual `Custom DocPerm` overrides for Production Batch before publishing the final matrix.
- Force reloads restricted Page metadata so Administration Console, Document Studio and Launch Center remain management-only.
- Rebuilds the WAFD ONE workspace and clears permission/workspace caches.
- Does not modify project records, completed workflows, invoices, payments or historical operational documents.

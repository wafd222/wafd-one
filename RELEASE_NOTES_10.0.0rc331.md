# WAFD ONE 10.0.0 RC331

## Orphan Iftar Supervisor assignment repair

- Fixes the mobile error raised when a Supervisor Plan or Daily Report still points to a deleted Iftar Project.
- Keeps valid Supervisor tasks visible even when an old test assignment is stale.
- Removes only orphan assignment records during migration; valid operational data is unchanged.
- Prevents future orphan assignments when an Iftar Project is permanently deleted.
- Keeps all RC330 page-loading and camera-only evidence behavior unchanged.

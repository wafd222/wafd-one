# WAFD ONE 10.0.0 RC110 — Deploy Performance

- Removed duplicate full DocType synchronization from every `after_migrate`.
- Removed automatic 400+ hotel catalogue scans and updates from normal upgrades.
- Stopped force-rebuilding the Workspace on every deployment.
- Kept installation and explicit repair routines available.
- Added optional `wafd_one_full_post_migrate` recovery mode for damaged sites only.
- No business workflow or user data was removed.

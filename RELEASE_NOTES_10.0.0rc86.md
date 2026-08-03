# WAFD ONE 10.0.0 RC86

- Restored the standard Frappe two-level package/module layout.
- Kept app hooks and Python services in `wafd_one/`.
- Moved module metadata under `wafd_one/wafd_one/` so Frappe can import `wafd_one.wafd_one`.
- Corrected setup and historical patch paths for DocTypes, Workspace, Pages, and Print Formats.

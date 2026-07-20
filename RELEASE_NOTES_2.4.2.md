# WAFD ONE 2.4.2

- Corrected migration order for Phase 1 metadata.
- Creates WAFD roles before Frappe model synchronization.
- Repairs Phase 1 DocTypes in child-first dependency order.
- Reloads the standard WAFD ONE Workspace using Frappe's metadata loader instead of manually inserting it.
- Adds a new one-time repair patch for sites upgraded from 2.4.1 and earlier.

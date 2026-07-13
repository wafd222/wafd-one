# WAFD ONE v2.1.1

## Frappe v16 installation fix

- Adds the mandatory `type` field to the WAFD ONE Workspace.
- Sets the Workspace application owner to `wafd_one`.
- Normalizes Workspace data during `after_install` and `after_migrate` for compatibility with Frappe v16.
- Fixes site creation failure: `MandatoryError: [Workspace, WAFD ONE]: type`.

# WAFD ONE v2.1.2

- Fixed Frappe v16 site installation failure caused by an empty mandatory Workspace `type` field.
- Explicitly sets Workspace `type` to `Workspace` and app to `wafd_one`.
- Keeps existing Workspace records synchronized with the corrected fields.

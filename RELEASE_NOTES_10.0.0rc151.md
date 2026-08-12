# WAFD ONE 10.0.0rc151 — Centralized Permissions Hardening

- Restores WAFD DocType permissions from the application source on migrate by removing stale `Custom DocPerm` overrides created through Role Permission Manager.
- Makes `WAFD Recipe` read/print/report-only for `WAFD Production Supervisor` and `WAFD Storekeeper`.
- Keeps recipe master maintenance with `WAFD Operations Manager` and `System Manager`.
- Adds server-side defense-in-depth to block unauthorized recipe create/update/delete even if a user reaches a direct form URL.
- Preserves trusted internal maintenance flows that explicitly run with `ignore_permissions`.

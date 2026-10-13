# WAFD ONE 10.0.0 RC356

- Delivery Viewer language isolation only: language selection on the Delivery Data screen now uses a dedicated local storage key and never changes the global WAFD language preference.
- Delivery Viewer language switching remains fully client-side and supports all ten WAFD languages without calling Frappe/MariaDB.
- Preserves all RC354 behavior and permissions.
- No changes to role-home behavior, roles, task assignments, delivery workflows, Iftar workflows, driver functions, undertakings, or business logic.

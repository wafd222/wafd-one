# RC392 — Explicit opt-in for Iftar external viewers

Based on RC391. Changes limited to the Employee Management Iftar project viewer picker and its option provider.

- Viewer options list active registered employees, rather than mixing in all role-based management accounts.
- Remove the misleading “task will be added automatically” suffix from viewer candidates only.
- Clarify that external monitoring appears only after management explicitly selects and saves each project viewer; removing selection revokes project access.
- Existing RC391 per-project membership checks, unlimited viewer selections, and all operational assignments are unchanged.
- On explicit save, the necessary viewer role can still be prepared for a selected employee, without replacing their other tasks. This is not automatic assignment to an unselected employee.
- Frappe v16 compatibility range is retained.

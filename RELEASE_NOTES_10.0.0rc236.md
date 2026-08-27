# WAFD ONE 10.0.0 RC236

## Unified employee account and task management

- Adds a manager-only **Employee Management** page to the mobile WAFD ONE home.
- Creates independent Frappe System User accounts using employee name, unique email, temporary password and assigned task.
- Supports multiple employees in the same operational task.
- Provides task choices for project management, production, quality, warehouse, cleaning, delivery, drivers, finance, approvals, audit and undertakings.
- Deliberately excludes System Manager and Operations Manager from assignable tasks to prevent privilege escalation.
- Lists managed employees with email, assigned task and active/disabled status.
- Allows managers to change an employee task without retaining obsolete WAFD operational roles.
- Allows immediate disable/reactivate; disabling invalidates all active sessions while preserving operational history.
- Automatically creates or links the WAFD Driver master record when the Driver task is selected, including required mobile number.
- Marks linked driver records inactive when the account is disabled or moved to another task.
- Keeps the existing Undertaking Team page and APIs for backward compatibility.
- Preserves RC235 iPhone PWA header behavior and all existing operational workflows.

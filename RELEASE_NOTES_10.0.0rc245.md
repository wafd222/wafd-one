# WAFD ONE 10.0.0 RC245

## Explicit trip assignment and employee access audit

- Adds a stable hidden `assigned_driver_user` link to every delivery trip instead of depending on mutable driver names or mobile values at display time.
- Migrates legacy trips to the unique enabled Driver user using direct links first, then exact mobile/name matching, then an exact unique full-name fallback.
- Repairs unassigned legacy trips again when the driver opens **My Trips**, covering older data even if it was created outside the standard workflow.
- Makes new trips store both the canonical WAFD Driver record and the assigned login account.
- Applies the same assignment to trip lists, document permissions, delivery proofs and private delivery images.
- Tests all 12 managed employee roles and all 56 tools shown on their role-home screens against installed Page and DocType permissions.
- Fixes the Auditor cards for invoices and payments by adding the missing read-only permissions.
- Keeps disabled accounts blocked and prevents ambiguous duplicate names from being assigned automatically.

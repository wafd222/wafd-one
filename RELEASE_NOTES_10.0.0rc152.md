# WAFD ONE 10.0.0 RC152 — Comprehensive Permissions Baseline

RC152 completes the role-permission consolidation started in RC151.

## Scope
- Re-audited all non-child WAFD DocTypes and every WAFD role.
- Applied least-privilege ownership: operational roles can edit their own workflow area and only read dependent/cross-functional records.
- Recipe management remains restricted to System Manager / WAFD Operations Manager; Production Supervisor and Storekeeper are read-only.
- Quality, production, delivery, store, finance, project, approval and audit duties are separated.
- Removed broad email/export/share capabilities from ordinary operational roles unless required.
- Standard lookup visibility added for Item, Item Group, UOM and Warehouse where required by store/production/finance workflows.
- WAFD custom permissions are reloaded from app metadata during migration and stale WAFD Custom DocPerm overrides are cleared.

## Security design
- System Manager retains administrative control.
- WAFD Operations Manager retains operational control with deletion limited on business transactions.
- WAFD Auditor is read/report/export only.
- WAFD Approver is limited to approval requests.
- Cross-functional roles default to read/print/report instead of write/create.

## Validation
- JSON permission metadata audit for all WAFD non-child DocTypes.
- No ordinary WAFD role receives delete/import by default.
- Recipe create/write remains denied to Production Supervisor and Storekeeper.
- Python compilation and ZIP integrity checks performed before packaging.

# WAFD ONE v6.0.1

Stability review for governance, approvals, and audit controls.

- Enforces the configured approver role instead of a hard-coded role.
- Blocks repeated decisions on finalized approval requests.
- Requires reasons for rejection and cancellation.
- Prevents self-approval in both API and document paths.
- Makes audit events immutable at the controller level.
- Adds a dedicated cancellation audit event.
- Validates non-negative approval thresholds and audit retention settings.
- Aligns package, application, and README version metadata.

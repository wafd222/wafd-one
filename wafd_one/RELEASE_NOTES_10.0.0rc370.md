# WAFD ONE 10.0.0rc370 — Iftar Authority Receipt Timeline

## Scope
Focused update to the Iftar external authority viewer only. No unrelated modules or operational records are changed.

## Changes
- Reworked the external authority viewer into a compact operational receipt timeline with nine requested stages: preparation/loading, in-transit delivery, at-site arrival, authority inspection, table-owner receipt, meal distribution, table raising/closeout, food-preservation handover, and final report.
- Completed stages show a green check and the recorded timestamp where available; pending stages remain visually neutral.
- Added the requested top summary table: contracting entity, site, table owner, table-owner mobile number, supervisor, and meal quantity.
- Reduced duplicate detail by collapsing per-owner photo/signature evidence and delivery trip details until requested.
- Made the final-report stage open the official report preview when final approval and closeout requirements are satisfied; retained a dedicated share action for the approved PDF.
- Extended the read-only monitoring payload with supervisor daily-report milestones, closeout photo/time, distribution photo/time context, preservation quantities/evidence, and table-owner mobile numbers.
- Preserved the existing role and project-assignment restrictions on the external viewer.

## Validation
- Iftar workflow contract and commercial pricing tests: 24/24 passed.
- Updated JavaScript syntax check and Python compilation passed.
- Full Frappe Cloud/browser role testing remains required before production deployment.

# WAFD ONE 10.0.0rc376 — Iftar Supervisor Workflow Permission Repair

- Fixes a role-overlap bug where a user assigned as the supervisor for a report and also carrying the Site Manager role was incorrectly blocked from saving table-owner handovers and supervisor evidence.
- Keeps the Site Manager restriction for reports assigned to other supervisors; Site Managers can review/approve without editing supervisor-owned details, photos, or signatures.
- Allows the assigned supervisor to complete table-owner handover evidence, distribution and closeout photos, and food-preservation receipt evidence so the final report can pass its ordered validations.
- Leaves the required workflow sequence intact: table-owner handovers must be confirmed before submitting the supervisor report, and all quantities/evidence must reconcile.
- Limits changes to the Iftar supervisor report controller and its regression test; no hotel delivery workflows or unrelated modules changed.

Validation: focused workflow contract tests, Python compilation, JavaScript syntax checks, and ZIP integrity checks are run locally. Live Frappe Cloud acceptance testing remains necessary.

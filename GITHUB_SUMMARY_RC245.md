## WAFD ONE 10.0.0 RC245 — Explicit Trip Assignment & Employee Access Audit

RC245 replaces inferred driver matching with a stable login assignment stored directly on every delivery trip. It migrates existing trips, self-repairs older unassigned records when the driver opens My Trips, and applies the same assignment to delivery proofs and private images.

### Included fixes

- Adds `assigned_driver_user` to WAFD Delivery Trip.
- Backfills existing trips to the unique enabled Driver account.
- Stores the assigned login on all new trips.
- Fixes driver trip listing, row permissions, proof access and evidence-image access.
- Validates all 12 managed employee roles and 56 home-screen targets.
- Adds missing read-only Invoice and Payment permissions for WAFD Auditor.

### Verification

- Explicit driver assignment regression test passed.
- Employee access matrix passed: 12 roles and 56 targets.
- Python, JavaScript, JSON, release metadata and all 180 patch paths validated.

### Deployment

Install/update the app and run `bench --site <site-name> migrate`. Then clear cache and fully close/reopen the driver PWA before opening **My Trips**.

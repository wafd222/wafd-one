## WAFD ONE 10.0.0 RC246 — Deterministic Driver Trip Retrieval

RC246 fixes **My Trips** by removing the ambiguous combined Frappe filter query. Trips are fetched internally and securely filtered against the signed-in Driver account before any data is returned. Missing or obsolete disabled assignments are repaired automatically, while assignments to another enabled driver remain protected.

### Included fixes

- Deterministic server-side trip filtering for the signed-in driver.
- Automatic repair of NULL and disabled legacy assignments.
- Compatibility with early records that used a login identifier.
- No cross-driver data exposure.
- Complete employee-role and operational permission regression tests.

### Deployment

Install/update the app and run `bench --site <site-name> migrate`. Clear cache, then fully close and reopen the driver PWA before opening **My Trips**.

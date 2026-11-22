# WAFD ONE 10.0.0 RC395 — Driver meal-run stale lock

- **Fix scope:** driver delivery queue only. Driver portal requests no longer auto-recreate deleted delivery trips from retained approved-loading records. This prevents deleted trip/run records from being resurrected on driver refresh and re-blocking subsequent meals.
- Manager reconciliation remains available from manager workflow for approved loadings that legitimately need trip recovery.
- No UI, role, permission, schema, or other workflow changes.
- **Verification:** Python syntax compilation and targeted regression test for the driver-vs-manager reconciliation behavior. Live Frappe Cloud behavior still requires deployment and validation.

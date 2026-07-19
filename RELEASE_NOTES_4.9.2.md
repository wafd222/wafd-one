# WAFD ONE 4.9.2

## Madinah Central Area hotels — phase one

- Added a dedicated audited reference file containing 115 unique hotel records identified inside the Madinah Central Area.
- Covered northern, southern, western and general Central Area zones.
- Added an idempotent migration patch that creates missing hotels and enriches existing records without deleting operational data.
- Recorded Booking, Expedia and Agoda directory references, verification status and review date.
- Tourism licence numbers remain blank unless an official licence identifier is available; platform appearance is not treated as proof of licensing.
- External Madinah hotels are intentionally deferred to phase two.

Reference file:
`wafd_one/reference_data/madinah_central_area_hotels_phase1.csv`

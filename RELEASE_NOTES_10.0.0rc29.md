# WAFD ONE 10.0.0rc29

## Production stability and safe deletion

- Audit events now retain the referenced document name as immutable text rather than a Dynamic Link, so audit history no longer prevents deletion of eligible source records.
- Audit events remain immutable and non-deletable.
- Late production completion is recorded as `متأخر / Delayed` and shown as a warning instead of blocking completion and the next workflow stage.
- Added migration patch `v10_0_0_rc29` for existing sites.
- Posted stock movements remain protected from deletion to preserve inventory integrity.

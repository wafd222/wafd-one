# WAFD ONE v4.9.3 — Official Central Area Hotel Map

- Added 191 unique hotel names transcribed from the supplied official central-area guide map.
- Added Central Map Number, Central Sector and Source Map Edition fields to WAFD Hotel.
- Added idempotent patch `wafd_one.patches.v4_9_3.execute.execute`.
- Existing operational records are updated, not deleted.
- Map verification is separate from tourism-license verification.

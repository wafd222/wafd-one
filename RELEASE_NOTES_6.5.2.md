# WAFD ONE 6.5.2

- Fix hotel catalogue migration failure caused by an unsupported Verification Status value.
- Normalize Zone, Proximity Band, and Verification Status against live WAFD Hotel Select options.
- Preserve verified source context in source fields without inventing unsupported Select values.
- Add an idempotent recovery patch for interrupted v6.5.0/v6.5.1 migrations.

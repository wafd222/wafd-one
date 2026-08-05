# WAFD ONE 10.0.0 RC98

- Fixes repeated RC96 migration failure caused by duplicate `WAFD-HC-00001`.
- Makes hot-cabinet creation idempotent and safe after partial migrations.
- Stops resetting the hot-cabinet naming series during migration.
- Preserves existing cabinet operational data while filling only missing cabinets through 50.

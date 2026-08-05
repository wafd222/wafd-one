# WAFD ONE 10.0.0 RC99

- Prevent migration failure when the optional Madinah hotel catalogue CSV is absent.
- Preserve all existing hotel records and skip only the optional seed import.
- Keep the RC98 idempotent hot-cabinet migration fix.
- Make after_migrate safe for repeated production deployments.

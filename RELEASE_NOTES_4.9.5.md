# WAFD ONE 4.9.5

## Migration reliability fix

- Fixed the v4.9.3 central-hotel import failure caused by an invalid Select value.
- Normalized map verification to `رسمي موثق / Official Verified`.
- Added defensive validation against live WAFD Hotel Select options before saving.
- Preserved idempotent hotel matching by hotel name and central map number.
- Re-audited Python syntax, JSON files, patch imports, and reference CSV values.

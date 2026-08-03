# WAFD ONE 6.6.2

## Critical migration fix

- Corrected the WAFD Document Template naming expression.
- Made the v6.6.0 template installation patch idempotent.
- Prevented duplicate primary-key errors during repeated or recovered migrations.
- Added a v6.6.2 recovery patch that safely ensures all starter templates exist.
- Preserved existing document templates and operational data.

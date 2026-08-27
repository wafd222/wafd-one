# WAFD ONE 10.0.0 RC230

## iPhone & Android PWA release hardening
- Audited and hardened the PWA already present in RC229.
- Corrected manifest start/id to `/wafd-mobile`, the existing role-aware launcher.
- Staff/managers launch to WAFD role home; client users launch to their portal; guests return through login.
- Keeps standalone display and existing Apple/Android/maskable icons.
- Adds standalone-state detection without changing operational workflows.
- Intentionally avoids offline caching of ERP transactional forms to prevent stale operational data.
- No schema change and no new migration patch.
- Preserves RC229 explicit hotel-add workflow and all validated undertaking/hotel fixes.

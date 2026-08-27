# WAFD ONE 10.0.0 RC231

## Final iPhone & Android PWA pre-upload QA
- Based strictly on RC230; operational ERP code is unchanged.
- Fixes Android install UX: removes the unsupported suppression of Chrome's native `beforeinstallprompt` flow when no custom install button exists.
- Keeps the role-aware `/wafd-mobile` launch route and standalone display mode.
- Explicitly sets `prefer_related_applications` to false.
- Preserves Apple touch icon, Android 192/512 icons and maskable icon.
- No service-worker/offline caching is introduced, avoiding stale transactional ERP data.
- No schema change and no new migration patch.

# WAFD ONE 10.0.0 RC178

## Mobile install / PWA enablement
- Added installable web app manifest for WAFD ONE.
- Added WAFD ONE branded 192px, 512px, maskable, and Apple touch icons.
- Added iOS standalone/mobile-web-app metadata and Android/Chromium install metadata.
- Added a role-aware `/wafd-mobile` launch route:
  - internal WAFD users -> role-based mobile dashboard
  - beneficiary/client portal users -> `/wafd-client`
- Enabled the PWA metadata on both Desk/mobile employee screens and the external client portal.
- No operational workflow, permission, inventory, finance, or client-portal security logic changed.

# WAFD ONE 10.0.0 RC232

## iPhone installed-PWA home chrome fix
- Based strictly on RC231; ERP workflows, permissions, hotel catalogue, undertaking logic and database schema are unchanged.
- Detects installed/standalone mode on both iOS (`navigator.standalone`) and Chromium (`display-mode: standalone`).
- Hides only Frappe's global Desk navbar on the WAFD role home when running as an installed mobile PWA.
- Keeps the navbar available in normal browser/desktop use and keeps transactional/form pages unchanged.
- No migration patch and no service-worker/offline caching changes.

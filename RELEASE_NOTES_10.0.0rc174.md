# WAFD ONE 10.0.0 RC174

## Client delivery timing integrity
- Delivery duration is calculated only from actual events belonging to the same operational Delivery Trip window.
- Reject stale legacy/test timestamps from earlier or unrelated dates instead of displaying misleading multi-day durations.
- Allow legitimate overnight trips with a controlled grace window after midnight.
- Sanitize actual departure/arrival/receipt times returned to the client portal so invalid historical timestamps are not exposed as current operational times.
- Keep receipt confirmation, receiver name/title and received quantity intact even when legacy timestamps are not comparable.

## Multilingual beneficiary portal
- Added a persistent language selector for Arabic, English, Indonesian, Urdu, Hindi, Bengali, French (Africa/Mali), Hausa, Swahili and Uzbek.
- Translate beneficiary portal navigation, project summaries, tracking stages, delivery timing, receipt confirmation, errors and privacy messages.
- Arabic and Urdu use RTL layout; other languages use LTR automatically.
- Language choice is stored on the device and reused on later visits.

## Multilingual employee mobile role home
- Added the same persistent language selector to the role-based employee mobile home.
- Role names and main operational task labels are localized for the supported workforce languages while preserving the exact underlying permissions and routes.
- No role, permission, workflow, finance, inventory or project-isolation rule was broadened by this release.

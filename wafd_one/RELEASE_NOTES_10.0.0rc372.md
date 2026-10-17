# WAFD ONE 10.0.0rc372 — Iftar Viewer Report & Navigation Fix

- Fixes the Iftar external viewer final-report failure path: if the standard Print Format record is not synchronized on an upgraded site, the server renders the same bundled official report template as a safe fallback. Project assignment, approval, dispatch, and closed-operation checks remain mandatory.
- Shows server error details in the report failure page instead of replacing them with a generic assignment message, and provides a reliable return action.
- Removes the mobile home-card navigation lock that could remain set when iOS suspends timers while the user views a report in another tab. The Iftar viewer card remains tappable after returning to the app.
- No hotel delivery records, normal delivery viewer permissions, or unrelated modules are changed.

Validation: Python compilation, JavaScript syntax checks, and Iftar workflow contract tests run locally. Live Frappe Cloud behavior still requires deployment acceptance testing.

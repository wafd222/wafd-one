# WAFD ONE 10.0.0rc371 — Iftar Authority Access Isolation

- Introduces the dedicated `WAFD Iftar Authority Viewer` role. Iftar-only assignment no longer grants or depends on the normal `WAFD Delivery Viewer` role.
- Removes the Iftar tracking card from the normal Delivery Data profile and provides a separate Iftar-only profile. Users see both only when they independently have both tasks.
- Employee Management project assignment now prepares the dedicated Iftar viewer role for the selected user. Existing submitted Iftar assignments are migrated on deployment; the old delivery-viewer role is removed only when that account has no active delivery-tracking shares. Delivery share records are never changed.
- The authority monitoring and approved report endpoints remain read-only and strictly project-assignment scoped.
- Improves the monitoring page's error display to show the server response and retry action rather than a blank page with a generic message.
- Normal hotel delivery pages, trip records, delivery shares, and unrelated project data are not modified.

# RC383 — External Iftar viewer and report preview stability

- Re-entry: if iOS restores the home screen while Frappe still tracks the external viewer route, the viewer card now transitions through home and opens the viewer again.
- Report preview: opens inside WAFD ONE with clear Back, Print, and Share controls, avoiding the separate Safari/PDF window lifecycle that could leave the viewer unresponsive.
- Report layout: allow sections to flow between A4 pages instead of pushing large blocks to the next page or forcing a page break, reducing blank space while retaining the existing report content and evidence.
- Scope: limited to the external Iftar viewer card and its approved final report. No roles, permissions, or operational workflows changed.
- Validation: JavaScript syntax checks passed; 7 focused navigation/report assertions and 27 Iftar workflow tests passed. Safari/iPhone live retest is still required after deployment.

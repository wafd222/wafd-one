# WAFD ONE 10.0.0rc135 — Final Mobile QA Hardening

This release is a QA-focused follow-up to RC134.

## Improvements
- Prevents the direct mobile stage-action button from covering operation fields by reserving bottom space and rendering the action in a safe fixed dock.
- Keeps one-tap stage progression on mobile while preserving the normal Frappe Save action.
- Reworks the report-center day picker so iOS shows readable date/meal/status labels instead of technical `IFTAR-DAY-*` document IDs.
- Keeps the selected readable label mapped safely to the correct daily-operation document for PDF output.
- No business-rule changes to the approved 9 SAR standard meal pricing, optional-item pricing, project workflow, or print templates.

## QA
- Python syntax / compile validation
- JavaScript syntax validation
- JSON metadata parse validation
- Patch-path validation
- Release consistency validation
- ZIP integrity validation

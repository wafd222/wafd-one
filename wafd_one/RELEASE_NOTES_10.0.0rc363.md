# WAFD ONE 10.0.0 RC363

## Focused fix: official Iftar report preview for external viewers
- Replace the direct-print action in the external authority monitor with an official-report preview screen.
- Reuse the existing `WAFD Iftar Official Daily Report` print format already used by the project-manager workflow, preserving its full report sections, stage details, delivery evidence/photos, signatures, and approval metadata.
- Add explicit Back, Print, Share, and Download PDF controls on the preview screen; printing no longer launches automatically when the user taps the report button.
- Keep report actions available only after the operation is closed, the final administration approval is recorded, and the report has been sent.
- Add server-side checks for the external viewer role, exact project assignment, published project state, and final report approval before rendering HTML or PDF. The endpoints are read-only.

## Scope protection
Only the Iftar authority viewer page assets and additive official-report helper endpoints in `iftar_stage_portal.py` were changed. No existing workflow, data, permissions for unrelated modules, hotel delivery screens, inventory, finance, or employee-assignment behavior was intentionally changed.

## Validation
- Python source compilation: passed.
- JavaScript syntax check: passed.
- JSON syntax and ZIP integrity: checked before delivery.
- The Frappe Cloud runtime, final-report rendering with real delivery photos, and iPhone native print/share behavior still require staging verification after deployment.

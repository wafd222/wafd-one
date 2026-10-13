# WAFD ONE 10.0.0 RC359

## Focused corrections to the authority Iftar monitoring screen
- Route the existing external-viewer home card to the dedicated read-only authority monitoring page.
- Restrict external viewers to submitted/approved projects explicitly assigned to their user account; management roles retain draft visibility for setup and review.
- Make the displayed production, packaging, loading, delivery, and site-receipt stage indicators reflect actual quantities/approval state rather than treating the kitchen-start flag as production completion.

## Scope
No unrelated modules or operational workflows intentionally changed. Based on RC358 with only the authority-monitoring route, access filter, and stage-indicator corrections.

## Validation
- ZIP archive integrity checked.
- Python source compilation checked.
- JSON and JavaScript syntax checks run before deployment.
- Frappe Cloud runtime, permissions, and real operational data still require staging verification after deployment.

# WAFD ONE 10.0.0 RC362

## Focused fixes: Iftar authority monitoring only
- Improved the operation-date and language controls on mobile so the date field remains readable and does not wrap awkwardly.
- Kept the authority monitoring data source limited to submitted WAFD Iftar projects and their linked Iftar daily operations and trips; hotel delivery tracking remains a separate workflow.
- Added final-report print and share controls to the authority read-only screen. These controls appear only when the operation is closed and the Project Manager's final report approval and dispatch flags are set.
- The print view contains the assigned Iftar project's daily totals, delivery details, and final approval/recipient information. Sharing uses the device's native share sheet when available, with a copy-to-clipboard fallback.
- Added the final approval metadata needed by the read-only screen.

## Scope protection
No unrelated modules, hotel delivery workflows, inventory, finance, staff assignment flows, or existing operational screens were intentionally changed. Changes are limited to the Iftar authority monitoring page, its data fields, mobile styles, and these release notes.

## Validation
- ZIP archive integrity checked.
- Python source compilation checked.
- JSON and JavaScript syntax checks checked before packaging.
- Frappe Cloud runtime behavior, browser printing/sharing, and real project data still require staging verification after deployment.

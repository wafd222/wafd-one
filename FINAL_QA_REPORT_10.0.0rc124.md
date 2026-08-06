# WAFD ONE 10.0.0 RC124 — Final Iftar QA

## Implemented
- Fresh four-step Iftar wizard; no stale values on page show/new project.
- Correct New Project route handling using `frappe.route_options`.
- Sequential route from creation to first Daily Operation.
- Flexible operating-cost agreements: cartons (25 meals/carton), tablecloths, supervisors manager, supervisors, assistants, packaging workers, loading workers, drivers, and one custom cost row at creation; full child table remains editable later.
- Carton quantity auto-recalculates from total meals and 25-meal capacity.
- Zamzam replaces ordinary water and carries approved 9 SAR reference cost when legacy cost is blank/1.5.
- Mosque/Haram packages exclude WAFD/Iftar branded outer wraps; external/entity distributions add them.
- Receipt dialog captures recipient, table owner, supervisor, supervisors manager, assigned meals, and 1–100 assistant attendance rows.
- Completion dialog offers Report Center, next operation day, or Operations Dashboard without forced navigation.
- Operations dashboard is charcoal/black with no mosque background image.
- Unified Report Center includes project summary, ingredients/pricing, costing/profitability, distribution/cartons, daily stage report, handover/receipt, supervisor/assistants, and daily record navigation.
- Iftar print formats rebuilt with conservative table-based A4 HTML/CSS, no CSS grid/flex in print documents, valid balanced HTML, embedded logo data URI, and explicit override of preview flex flow.

## Automated checks
- Patch path validation: passed (128 entries).
- Release validator: passed for 10.0.0rc124.
- JSON parse validation: passed.
- Python syntax validation: passed.
- JS syntax validation with Node: passed for all changed Iftar files.
- All 7 Iftar print-format HTML templates: balanced key tags; no external HTTP assets; no print grid/flex layout.

## Runtime verification note
Frappe Cloud still must render Preview and PDF on the deployed site to prove pixel-level equality because PDF generation is performed by the server PDF engine. RC124 removes the known template-level causes (invalid HTML, flex/grid print layout, external logo fetch, and preview flex flow mismatch).

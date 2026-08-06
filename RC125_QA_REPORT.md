# WAFD ONE 10.0.0 RC125 — Iftar Workflow QA

## Implemented
- Prophet's Mosque auto-fills contracting entity to the Haramain authority.
- Distribution site is auto-copied from the main site; external sites remain editable.
- Distribution type is derived automatically from the selected site.
- Standard Iftar selling price starts at SAR 9.00.
- Optional-item reference costs are loaded from WAFD Ingredient and added to the selling price automatically.
- Wizard Next/Create buttons use direct DOM listeners after render; no delegated page-container click dependency.
- Wizard is rebuilt cleanly on every page show.
- Report Center supports project, table-owner, and date search and no longer forces the latest project.
- Operations dashboard separates Projects Today from All Active Projects and shows both counts.
- Existing RC124 print-format files were intentionally left unchanged.

## Automated validation
- Python syntax: passed for all app Python files.
- JSON parse: passed for 89 JSON files.
- JavaScript syntax: passed for 34 JavaScript files.
- Patch registry: 129 executable entries, no missing module paths and no duplicates.
- RC125 functional source assertions: passed.
- RC124 vs RC125 print-format comparison: 14 print-format files compared, 0 changed.
- ZIP integrity: verified after packaging.

## Required cloud smoke test after Deploy + Migrate
1. Open New Iftar Project twice and verify the second form is clean.
2. Select Prophet's Mosque and verify contracting entity/site/type auto-fill.
3. Verify Standard Iftar = SAR 9.00; select add-ons and verify price increases.
4. Click Next through all four steps and Create Project; verify first daily operation opens.
5. Open Operations: verify Projects Today and All Active Projects tabs/counters.
6. Open Report Center: search by project, table owner, and date.
7. Re-check one existing print preview/PDF pair; RC125 does not modify RC124 print templates.

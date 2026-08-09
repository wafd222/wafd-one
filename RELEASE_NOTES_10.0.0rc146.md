# WAFD ONE 10.0.0 RC146 — Consolidated Final QA

## Finance / VAT consistency
- Project profitability now excludes output VAT from management revenue and profit.
- Invoice and payment totals remain VAT-inclusive for statutory billing and collection.
- Added explicit project fields for collected amount including VAT and collected VAT.
- Partial payments allocate net revenue and VAT proportionally to the linked invoice.
- Project Actual Revenue, Profit, Margin, Revenue/Meal and Profit/Meal now use VAT-exclusive revenue.
- Executive dashboard profitability uses invoice subtotal (before VAT), while invoice/collection KPIs keep gross VAT-inclusive amounts.
- Finance status clearly shows invoiced gross, collected gross, VAT, net revenue, actual cost and profit.
- Finance integrity check now detects invoice tax/grand-total inconsistencies.

## Estimated cost consistency
- When a project estimate is still zero, Financial Refresh derives it from saved Daily Meal Plan estimated costs.
- Saving a Daily Meal Plan refreshes the parent project financial rollup, so the project no longer stays at Estimated Cost = 0 when detailed planning already has a cost.
- A manually entered non-zero project estimate remains authoritative.

## Operational workflow hardening retained from RC145
- Daily Plan → Production → Packaging → Loading → Delivery state synchronization retained.
- Existing downstream documents are opened instead of recreated.
- Duplicate production/material actions remain blocked after progression to a later stage.
- Historical delivered chains are repaired idempotently during migration.

## Project certificate / print QA
- Rebuilt the project Service Acceptance & Appreciation Certificate with the official WAFD logo and cleaner bilingual identity.
- Removed repetitive mission/project wording and improved hotel/period/meal presentation.
- Project certificate print action resolves the configured default template dynamically instead of relying on a hard-coded template name.
- Legacy OPERATION-ORDER template identifiers are no longer kept as the default project certificate when a clean certificate template can be created.

## Preserved Iftar Pro rules
- Standard Iftar selling price remains SAR 9.00 VAT-inclusive.
- Zamzam remains SAR 1.50 cost-only and replaces ordinary water without changing selling price.
- Standard meal packaging remains inside meal cost.
- Haram selector remains location-only (no company names/codes).
- Supervisor/team reusable rosters, attendance distinction, report-center dropdown cleanup, official report readiness checks and Executive Gray mobile UI are preserved.

## Release hygiene
- Version normalized to 10.0.0rc146 in both package metadata files.
- RC146 migration patch refreshes workflow states, financial rollups, project certificate metadata and cache.
- Python bytecode/cache files are removed before packaging.

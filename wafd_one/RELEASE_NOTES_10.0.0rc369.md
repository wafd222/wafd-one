# WAFD ONE 10.0.0 RC369 — Iftar Workflow Hardening

## Scope
- Based on the submitted RC367 package and the focused RC368 corrections.
- Changes are limited to Iftar project pricing and Iftar role portals; no unrelated application modules or user data are changed.

## Included corrections
- Preserve the editable VAT-inclusive standard base price separately from package surcharges and paid add-ons.
- Restore the base price when returning to Standard Iftar; clear the Zamzam toggle and optional add-ons on that transition.
- Keep the final sale price, gross revenue, VAT portion, net revenue, and profitability on the same pricing rule.
- Restore SAR 9 as the safe base price for legacy project records whose stored base price is numeric zero; new project creation still rejects non-positive prices.
- Make authority inspection approval (photo, signature, and required food checks) a mandatory gate before supervisor tasks can be created or meals handed to supervisors. Site receipt no longer creates supervisor tasks prematurely.
- Reuse the previous supervisor roster with its actual user accounts and active status. Reuse meal/supply allocations only when the new daily meal total matches; otherwise preserve people and owners but reset incompatible quantities for manager review.
- Keep the external authority view read-only and project-scoped, show supervisor evidence photos, and remove duplicate project-card operational details.

## Validation performed locally
- 24 focused pricing/workflow regression tests.
- Python syntax compilation across the app.
- JavaScript syntax checks across the app.
- JSON parsing across app metadata files.
- ZIP integrity check.

## Not claimed as live-tested
- Live Frappe Cloud database writes, role permissions under real accounts, mobile camera/signature capture, scheduled daily-operation creation, and final PDF/share behavior require deployment to a staging site and test accounts.

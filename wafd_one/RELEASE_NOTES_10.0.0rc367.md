# WAFD ONE 10.0.0 RC367 — Iftar Price Reset Fix

## Focused changes
- Keeps the manager-entered base selling price in wizard state while selecting meal templates and add-ons.
- Calculates the visible VAT-inclusive price from the saved base price plus currently selected paid add-ons.
- Adds the SAR 1.50 Iftar + Zamzam package surcharge, while Zamzam still replaces ordinary water in the recipe.
- Switching back to Standard Iftar clears meal add-ons and Zamzam selection and restores exactly the manager-entered base price.
- Aligns server-side project price recalculation with the wizard calculation so revenue and VAT use the same final selling price.

## Scope protection
- Functional changes are limited to the Iftar wizard price logic, Iftar project price recalculation, and project-creation price normalization.
- No unrelated screens, modules, roles, inventory flows, documents, or reports were intentionally changed.

## Validation
- JavaScript syntax check and Python compilation passed.
- ZIP integrity and focused price arithmetic tests passed.
- Live Frappe Cloud workflow was not executed in this environment; validate in staging before production deployment.

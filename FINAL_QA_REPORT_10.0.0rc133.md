# WAFD ONE 10.0.0 RC133 — Final QA

## Scope
Focused correction after RC132: Iftar selling price and UX refresh for Project Wizard, Daily Operations, and Report Center. Existing print formats/documents were intentionally left unchanged because the current documents were user-validated.

## Pricing checks
- Base Standard Iftar selling price is server-owned at SAR 9.00.
- With no selected add-ons and no Zamzam replacement, server forces SAR 9.00.
- Only explicitly checked meal add-ons are included in the commercial selling price.
- Removing an add-on removes its surcharge; removing the final add-on returns the price to SAR 9.00.
- Zamzam adds only the positive replacement difference between Zamzam and ordinary water.
- Carton, tablecloth, supervisors, assistants, packaging/loading workers, drivers and other operating costs remain project costs and are not added to sale_price_per_meal.

## UX checks
- Wizard rebuilt around explicit add-on checkboxes instead of MultiCheck internal state.
- Wizard, operations and report center use a unified charcoal / grey / muted-gold WAFD visual system.
- Responsive mobile breakpoints retained.
- Report card mappings and print formats were not changed.

## Technical checks
- Python compileall: PASS.
- JavaScript syntax check (wizard / report center / operations): PASS.
- Daily-photo DocType controller package exists (RC132 migration hotfix retained).
- No new DocType schema or patch was introduced in RC133.
- Version bumped to 10.0.0rc133 in pyproject.toml and wafd_one/__init__.py.

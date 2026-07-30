# WAFD ONE 10.0.0rc28

## Meal plan recipe resolution repair

- Resolves production recipes from the direct meal-plan link first.
- Repairs legacy plans from their linked daily-plan row.
- Falls back only to an exact, unique active recipe-name match.
- Backfills the resolved recipe link on legacy meal plans.
- Prevents silent selection when recipe names are ambiguous.
- Improves the operator error message when no safe recipe match exists.

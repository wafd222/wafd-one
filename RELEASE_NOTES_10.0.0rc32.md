# WAFD ONE 10.0.0rc32

## Stability consolidation

- Canonicalized bilingual UOM values across ingredient master, purchase orders,
  stock movements and stock balances.
- Legacy aliases such as `Kg`, `كجم` and `كجم / Kg` are treated as the same
  unit while genuinely incompatible units remain blocked.
- Stock movement UOM is now read-only and fetched from the ingredient master.
- Existing compatible stock-balance UOM values are repaired during normal
  stock posting without changing quantities or costs.
- Preserves RC28–RC31 fixes for recipe resolution, material allocation,
  migration, audit references, non-blocking deadline warnings and automated
  quality/CCP/food-safety workflow.

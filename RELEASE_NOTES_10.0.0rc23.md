# WAFD ONE 10.0.0rc23

## Production automation and guided progression

- Production Batch now loads the project, daily plan, recipe, production date, quantity, kitchen and warehouse sources immediately after selecting a Meal Plan.
- Recipe material requirements, allocations, availability and estimated material cost are displayed before the first save.
- Production Date no longer remains blank when the Meal Plan has a service date.
- Source warehouses are inherited from the Daily Plan and supplemented by recipe-category warehouse mapping.
- Safe automatic navigation was added after saving an operational stage:
  - Production → Packaging only after production readiness, passed quality and food-safety release.
  - Packaging → Loading only when packaging is complete or ready for loading.
  - Loading → Delivery Trip only after loading is confirmed.
  - Delivery Trip → Delivery Proof after arrival/delay state.
  - Accepted Delivery Proof → Invoice based on delivered quantities.
- Safety, quality, stock and mandatory-data gates are not bypassed by automatic navigation.

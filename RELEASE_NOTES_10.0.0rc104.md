# WAFD ONE 10.0.0 RC104

## Iftar project workflow corrections

- Draft Iftar projects can now be saved before carton generation.
- Blank manually-added carton rows are discarded safely.
- Cartons are generated automatically when recipient allocations equal the distribution plan.
- Carton numbering and meal quantities are populated automatically and partial cartons are supported.
- Existing carton status, vehicle, and notes are preserved when the generated plan is unchanged.
- Vehicle selection is limited to available company fleet records and shows plate/type/model details.
- Meal component UOM and cost continue to load from inventory; missing costs can be entered as actual costs.
- Submission is blocked if a mandatory component still has zero cost.
- Operating-cost child form is simplified while preserving compatibility fields internally.
- Distribution recipient rows now include delivery location, scheduled time, receiver name, and receipt signature.

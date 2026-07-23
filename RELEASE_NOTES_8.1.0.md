# WAFD ONE v8.1.0

## Contract finance corrections
- Contract Value is now explicitly treated as the agreed value before VAT.
- VAT, grand total, advance payment, and outstanding balance update immediately.
- Server-side validation recalculates the same values on save.
- Added a read-only Grand Total field.

## Kitchen management
- Added WAFD Kitchen master data with capacity, production lines, manager, warehouse, and working hours.
- Converted Responsible Kitchen fields in contracts and projects to links.
- Migration creates WAFD Main Kitchen with 10,000 meals/day capacity.

## Contract to project
- Existing Create Project button remains available on saved contracts.
- Grand total and kitchen are transferred to the generated project.

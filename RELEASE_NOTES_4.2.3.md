# WAFD ONE 4.2.3

## Project, hotel, and meal-plan relationship corrections

- Removed the invalid `WAFD Hotel.mission` query that caused a Frappe permission error.
- Added a primary hotel field to contracts and catering projects.
- New projects now receive the contract hotel automatically and add it to the project hotels table.
- Contract updates synchronize the primary hotel and beneficiary count with the linked project.
- Meal plans now load allowed hotels from the selected project.
- A single project hotel is selected automatically.
- Existing projects without hotel rows are upgraded safely when their first meal plan is saved.
- Server-side validation prevents choosing a hotel that belongs to another project.

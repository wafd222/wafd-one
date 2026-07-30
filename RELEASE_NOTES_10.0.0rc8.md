# WAFD ONE 10.0.0rc8

- Fixed stale/out-of-range service dates in new daily meal plans.
- Uses the linked contract as the authoritative source for dates, hotel, beneficiaries, and meals.
- Automatically selects the first valid service day when an invalid date is supplied.
- Loads every active contract meal with quantity, recipe, service time, and price.
- Repairs existing pre-production projects from their linked contracts during migration.
- Preserves projects that have already entered production.

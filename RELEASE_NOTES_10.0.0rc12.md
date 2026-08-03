# WAFD ONE 10.0.0rc12

## Inventory master-data completion

- Creates missing ERPNext Item records for every WAFD ingredient.
- Creates required ERPNext UOMs and WAFD item groups idempotently.
- Creates the ten operational warehouses under a dedicated WAFD warehouse group for the default company.
- Creates zero-quantity WAFD Stock Balance placeholders in the appropriate warehouse for each ingredient.
- Never fabricates opening stock; quantities remain zero until an approved physical count or stock movement is posted.
- Extends Install Missing Master Data so the same safe installer can be run again at any time.

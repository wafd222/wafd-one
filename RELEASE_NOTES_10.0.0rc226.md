# WAFD ONE 10.0.0 RC226

## Mobile hotel creation fix

- Fixes the native `Create a new WAFD Hotel` flow opened from the undertaking Hotel link.
- Enables Frappe Quick Entry for WAFD Hotel so mobile users see a compact saveable hotel form instead of landing mid-way through the full Hotel form.
- The first required fields are:
  1. اسم الفندق بالعربي / Arabic Hotel Name
  2. اسم الفندق بالإنجليزي / English Hotel Name
  3. الحي / District (optional)
- Removes the duplicate legacy Hotel Name field from the visible form. It is generated automatically from the Arabic name and remains the internal compatibility value.
- New WAFD Hotel document names are generated from the Arabic hotel name.
- Adds a mobile fallback that scrolls/focuses the Arabic name field if a full Hotel form is opened instead of Quick Entry.
- Preserves RC224 officer create permission and RC225 bilingual catalogue/search/share behavior.

## Migration
RC226 changes WAFD Hotel DocType metadata (Quick Entry, required fields, autoname and field visibility). Run migrate after deployment.

# WAFD ONE 10.0.0 RC122 — Print Parity Fix

- Force-syncs the actual database Print Format HTML instead of relying on model sync.
- Removes legacy signature markup that could remain in stored Print Format records.
- Uses self-contained deterministic A4 CSS shared by browser preview and PDF.
- Overrides Frappe preview flex behavior with `display:block` to reduce Preview/PDF layout drift.
- Uses mm/pt dimensions, fixed table layouts, predictable page breaks, and no Bootstrap layout dependency.
- Keeps letterhead disabled inside these formats because the WAFD header is rendered by the template itself.

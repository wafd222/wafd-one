# WAFD ONE 6.1.1 — Reviewed Master Data Safety Release

- Re-reviewed the complete v6.1.0 package and master catalogs.
- Permanently disabled both destructive full reset and reference-data deletion APIs.
- Removed unreachable deletion code from the reset endpoint.
- Added strict validation for required CSV catalog columns.
- Added strict validation for recipe JSON and ingredient rows.
- Verified 314 unique hotels, 120 unique ingredients, and 65 unique recipes.
- Verified all recipe ingredient links and supplier links resolve correctly.
- Removed compiled Python cache files from the distribution package.
- Preserved the non-destructive, idempotent install behavior.

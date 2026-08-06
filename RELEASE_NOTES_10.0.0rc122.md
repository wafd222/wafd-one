# WAFD ONE 10.0.0 RC122 — Migration Compatibility Fix

- Fixed RC121 migration failure on Frappe v16 sites where `Print Format.disable_letterhead` is unavailable.
- Print Format updates now inspect the live DocType metadata and write only supported fields.
- Removed the unsupported fixture key while preserving the unified Iftar print HTML/CSS.
- Kept RC121 patch path intact so previously failed migrations retry safely.
- Added compatibility handling for margin, letterhead, language, and alignment fields across Frappe v16 variants.

# WAFD ONE 10.0.0 RC133

- Fixed Iftar selling-price separation: Standard Iftar is always SAR 9.00 unless an explicit add-on or Zamzam replacement is selected.
- Replaced the fragile MultiCheck price source with explicit add-on checkboxes so removing every add-on deterministically returns the selling price to SAR 9.00.
- Server revalidates and recomputes the commercial selling price; carton, staffing, transport and operating costs never change the selling price.
- Refined the Iftar Project Wizard, Daily Operations dashboard, and Report Center with a dark charcoal / grey / muted-gold interface designed for lower glare while preserving WAFD identity.
- Report-center icons were normalized to restrained monochrome symbols and all existing report routes were preserved.
- Migration-safe follow-up to RC132; no DocType schema changes were introduced in this release.

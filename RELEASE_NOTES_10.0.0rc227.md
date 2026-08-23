# WAFD ONE 10.0.0 RC227

## Employee hotel creation
- Replaces metadata-dependent WAFD Hotel Quick Entry with a dedicated Frappe QuickEntry controller.
- Undertaking Officers always see Arabic Hotel Name, English Hotel Name and District, followed by Save.
- Re-applies the Undertaking Officer read/select/create permission during migration and removes stale Custom DocPerm overrides.
- Existing hotel edit/delete protection for undertaking officers is unchanged.

## Madinah hotel catalogue
- Consolidates the existing 400-row OTA catalogue and 204-row central/near-central catalogue.
- De-duplicates by normalized Arabic property identity.
- Produces 485 unique hotel/accommodation records, all with Arabic and English names.
- Corrects current names for selected properties against live Booking.com/brand sources.
- Existing site records are updated by normalized Arabic identity, including records whose English name was previously blank.
- Missing catalogue properties are inserted during migrate.
- Arabic and English names are both visible in the WAFD Hotel list and searchable.

## Scope note
The Saudi Ministry of Tourism reported 388 licensed hotels in Al-Madinah Province in H1 2025, while current OTA pages list a much larger number of "hotels and places to stay" because apartments, hostels and other accommodation types are included. RC227 therefore labels this as a comprehensive Madinah hotel/accommodation catalogue rather than claiming every OTA listing is a licensed hotel.

## Migration
Run migrate after deployment.

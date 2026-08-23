# WAFD ONE 10.0.0 RC225

## Bilingual hotel catalogue completion

- Reviewed the seeded Madinah hotel catalogues used by WAFD ONE.
- Added an explicit Arabic hotel-name field while preserving the existing primary hotel key.
- Completed Arabic and English name values for all 400 rows in the OTA review catalogue.
- Completed English values for all 204 central/near-central reference rows.
- Existing verified/canonical brand names are preserved where available; remaining names use standardized transliteration and are marked in the catalogue audit column.
- Hotel link search now searches Arabic name, English name, primary name, district, and central-map number as applicable.
- Newly added hotels from the undertaking screen require an English name and store the Arabic name explicitly.
- RC224 undertaking share-caption behavior is preserved: the share caption uses the hotel's English name while the PDF filename remains the undertaking number.
- RC224 officer hotel-create permission remains preserved.

## Sources reviewed
- Existing WAFD hotel reference catalogues and the 1448H/2026 central-area map dataset.
- Booking.com Medina accommodation listings for canonical/current English property naming.
- Agoda Medina accommodation listings for secondary OTA cross-checking.

## Migration
RC225 adds a DocType field and a data patch. Run migrate after deployment.

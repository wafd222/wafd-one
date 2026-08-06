# WAFD ONE 10.0.0 RC61

- Reworked contract reset/permanent-delete around the complete operational chain and retained transactional stock rollback.
- Added the approved 10 dry/operational warehouses and 4 cold/frozen rooms.
- Renamed compatible legacy warehouses while preserving document links.
- Added a preferred warehouse to every ingredient and automatic category/keyword routing.
- Created matching ERPNext warehouse masters and zero-balance placeholders safely.
- Existing non-zero stock is not silently moved during migration; physical relocation remains auditable through approved transfer movements.

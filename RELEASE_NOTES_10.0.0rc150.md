# WAFD ONE 10.0.0 RC150

## Production warehouse routing correction

- Corrected automatic ingredient-to-warehouse routing by material class.
- Raw fish/proteins now route to `ثلاجة 2 - اللحوم والدواجن والأسماك`, never the spice warehouse.
- Fresh vegetables such as bell/chili pepper route to `ثلاجة 1 - الخضار والفواكه` even though their names contain `فلفل`.
- Shelf-stable sauces/oils route to `مستودع 4 - المواد الغذائية المعبأة` before spice/fish keyword checks.
- Existing chilled routing for water/juice/dairy/date items is preserved; RC150 does not change that operating rule.
- Production allocation is now ingredient-specific and ignores stock held in an incompatible legacy warehouse instead of issuing from the wrong location.
- RC150 migration recalculates each ingredient's preferred warehouse.
- Only legacy RC50 acceptance-test opening stock is automatically transferred from a wrong warehouse to the corrected warehouse, using an auditable posted Transfer movement. Real/user-entered stock is never silently moved.
- Planned, unissued production batches are refreshed after migration so the corrected allocation appears immediately.

No print-format or financial/VAT logic was changed in this release.

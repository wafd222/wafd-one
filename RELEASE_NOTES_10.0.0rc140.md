# WAFD ONE 10.0.0 RC140

Focused QA correction after RC139 field testing.

- Fixed receipt-stage server error caused by the Distribution Recipient mobile field mismatch (`mobile_no`).
- Normalized existing Standard Iftar project selling prices during migration: SAR 9 VAT-inclusive plus only the six approved paid add-ons. Zamzam never raises the selling price.
- Kept Zamzam reference cost at SAR 1.50 and water-replacement behavior unchanged.
- Prevented project and daily-operation forms from becoming `Not Saved` merely by opening/refreshing them.
- Removed HTML list formatting that leaked raw markup into project Link/search dropdowns.
- Simplified Report Center project selection to clean plain-text dropdown labels with project number, site, dates and meals.

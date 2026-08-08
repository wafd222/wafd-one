# WAFD ONE 10.0.0 RC142

- Fixed report-center project dropdown labels that exposed legacy HTML fragments.
- Costing PDF now derives revenue from the current VAT-inclusive meal price × total meals, preventing stale cached revenue.
- Added migration repair for cached revenue, VAT, net revenue and expected profit.
- Preserved the SAR 9.00 VAT-inclusive Standard Iftar commercial price; Zamzam remains cost-only.
- Cleans legacy HTML contamination from stored project titles during migration.

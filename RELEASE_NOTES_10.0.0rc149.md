# WAFD ONE 10.0.0 RC149

## Migration hotfix — recipe source URL length

- Fixes the Frappe Cloud migration failure `CharacterLengthExceededError` on `WAFD Recipe.source_url`.
- Root cause: one official Bangladesh Tourism Board handbook URL is 161 characters while Frappe `Data` fields accept at most 140 characters.
- RC148 had failed before its patch was written to Patch Log, so RC149 hardens the RC148 patch itself; retrying migration will execute the corrected patch safely.
- Long source URLs are normalized to the stable official-domain URL for live `WAFD Recipe` records. The exact deep reference remains in `data_templates/recipes_reference_review.csv`.
- Adds defensive URL normalization to recipe master-data installation/update paths to prevent a future long reference URL from blocking migration.
- No changes to VAT, invoices, payments, pricing, profitability, document templates, or operational workflow.

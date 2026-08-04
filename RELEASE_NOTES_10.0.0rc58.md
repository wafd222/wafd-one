# WAFD ONE 10.0.0 RC58

- Safely reverses posted WAFD Stock Movements before contract reset or permanent deletion.
- Restores stock quantities and weighted-average valuation for Receipt, Issue, Transfer, and Waste movements.
- Blocks deletion when an Adjustment movement cannot be reversed safely instead of guessing or corrupting stock.
- Processes stock reversal before production-document deletion.
- Returns a completion report with reversed movement and item counts.
- Contract reset/purge remains transactional: any failure rolls the whole operation back.

# WAFD ONE 10.0.0rc26

## Material allocation repair

- Builds material allocations from live stock balances before creating issue movements.
- Searches all WAFD warehouses when recipe-category defaults do not contain the actual stock.
- Automatically adds the real stock warehouse to the production batch source list while preserving user priorities.
- Repairs older planned batches whose allocation child table was empty.
- Gives a precise validation message when recipe ingredient quantities or recipe yield are invalid.
- Keeps real stock-shortage controls in place; production never starts without sufficient posted stock.

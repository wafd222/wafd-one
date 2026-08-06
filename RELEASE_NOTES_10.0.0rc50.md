# WAFD ONE 10.0.0rc50

## Acceptance opening stock

- Adds an idempotent migration patch that initializes only zero-balance ingredients.
- Uses each ingredient's configured minimum stock and preferred warehouse.
- Preserves all existing positive balances without modification.
- Creates a posted adjustment movement for every affected warehouse for auditability.
- Marks generated balances clearly as acceptance-test opening stock requiring physical-count reconciliation before production use.

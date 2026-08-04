# WAFD ONE 10.0.0 RC64

## Immediate contract cleanup with stock settlement

- Contract permanent deletion now executes immediately after DELETE confirmation.
- Stock reversal blockers no longer stop deletion.
- Live stock balances are preserved exactly as they are.
- Quantities already issued or wasted remain consumed and are not recreated.
- Unused quantities remain in their actual warehouse or cold room without duplicate additions.
- The preview and success message show, per item and location: received, consumed, and unused retained quantity.
- Reset Test Data uses the same stock-safe settlement behavior.
- Cleanup remains transactional for linked document deletion.

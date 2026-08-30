# WAFD ONE 10.0.0 RC246

## Deterministic driver trip retrieval

- Replaces the combined `filters`/`or_filters` trip lookup with explicit server-side filtering before any row is returned to the driver.
- Repairs both empty assignments and assignments that still point to a disabled obsolete driver login.
- Supports early imported trips that stored the enabled Driver login as their driver identifier.
- Keeps enabled assignments to another driver protected and never overwrites them automatically.
- Preserves the manager field-delivery view, delivery photos, signatures, private files and multilingual workflow.
- Re-runs the complete 12-role employee access audit and operational permission checks.

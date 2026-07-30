# WAFD ONE 10.0.0rc28 — Audit Report

## Confirmed defect
Legacy/imported production batches could contain a Meal Plan but an empty Production Batch recipe link. The material workflow then stopped with “Select a recipe first,” even when an exact recipe was available through the linked daily plan or menu name.

## Implemented repair
- Direct Meal Plan recipe remains authoritative.
- Linked WAFD Daily Meal Plan Item recipe is used for legacy records.
- Exact active recipe document/name matching is allowed only when unique.
- Resolved recipe is backfilled to the Meal Plan.
- Ambiguous matches are blocked rather than guessed.
- Material requirement generation now invokes the same resolver.

## Validation
- Python AST/compile validation passed.
- JavaScript syntax validation passed.
- JSON parse validation passed.
- Patch path validation passed (80 entries).
- Release validation passed for 10.0.0rc28.

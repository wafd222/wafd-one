# WAFD ONE v8.2.0 — Automatic Meal Plan Engine

## Automatic schedule generation
- Generates meal plans directly from project dates, first meal, last meal, beneficiaries, and assigned hotels.
- No longer requires manual project service rows before generating the first operating schedule.
- Continues to respect explicit project service rows when they exist.
- Splits quantities across multiple hotels and validates that hotel guest allocations do not exceed beneficiaries.
- Uses safe default service times and avoids duplicate meal plans.

## Preview and safeguards
- Adds a pre-generation preview with day count, hotel count, meal-plan record count, and total planned meals.
- Protects plans that have already moved beyond Draft from destructive replacement.
- Shows missing-recipe warnings before production can begin.
- Updates project meal-plan counters and moves a Draft project to Planning after generation.

## User experience
- Adds a clear bilingual automatic generation action under Operations.
- Keeps manual meal-plan creation available only after planning has started or plans already exist.

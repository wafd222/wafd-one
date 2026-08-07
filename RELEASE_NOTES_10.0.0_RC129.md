# WAFD ONE 10.0.0 RC129 — Iftar Workflow Corrections

- Corrected contracting entity defaults: Prophet’s Mosque uses the General Authority for the Care of the Two Holy Mosques; Quba, Qiblatain and Miqat use Madinah Region Development Authority.
- Rebuilt wizard sale-price calculation as base 9.00 SAR + currently selected add-ons (+ Zamzam replacement difference) and server now stores the exact recomputed price, preventing stale higher prices after removal.
- Prevented reused table-owner allocations from exceeding a new project’s meal plan; allocations are copied only when the previous plan total exactly matches the new planned daily quantity.
- Improved add-on checkbox event handling so add/remove pricing updates after the native checkbox state is committed.
- Supervisor/assistant receipt now starts with 10 rows and expands automatically only when more assistants are recorded.
- Added a direct one-tap mobile next-stage action for production, packaging, loading, authority food inspection, delivery and receipt; users no longer need to open the three-dot menu for stage progression.
- Preserved the existing print parity templates from RC128.

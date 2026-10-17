# WAFD ONE 10.0.0rc375 — Allow Repeat Iftar Vehicle Trips

- Removes the one-vehicle-per-day restriction from the Iftar vehicle distribution plan.
- Allows the same driver to be assigned to multiple trips on the same day, supporting repeated loading and return trips.
- Each allocation remains a separate delivery trip and is validated independently against the vehicle's meal capacity.
- Keeps the reconciliation rule requiring the sum of all trip quantities to equal the loaded meal total.
- Keeps the 30-allocation safety limit, clarified as a trip-allocation limit rather than a unique-vehicle limit.
- Changes are limited to the Iftar distribution-plan workflow; hotel delivery workflows and unrelated modules are unchanged.

Validation: local regression test, Python compilation, JavaScript syntax checks, and ZIP integrity checks. Live Frappe Cloud acceptance testing remains required.

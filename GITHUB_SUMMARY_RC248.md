## WAFD ONE 10.0.0 RC248 — Delivery State and Driver Language Fix

RC248 closes the two remaining field-delivery issues. Saving a delivery proof
now persists the linked trip as Delivered with an updated modification time and
publishes Frappe's realtime document update so an open manager form refreshes.
The manager's proof action is idempotent and opens an existing proof even after
the trip has reached Delivered.

The cached My Trips page now re-reads the selected language whenever it is
shown, rebuilds its title, direction, controls and proof modal, and renders all
trip statuses and empty states in the selected one of ten supported languages.
A migration patch also repairs historical proof-backed trips left in Arrived.

Validation covers live delivery synchronization, existing-proof idempotency,
all ten language dictionaries, driver retrieval and identity isolation, the
full employee access matrix, patch paths, Python/JavaScript syntax, release
metadata, and the extracted ZIP payload.

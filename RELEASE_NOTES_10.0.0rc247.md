# WAFD ONE 10.0.0 RC247

## Root cause fixed

The driver page can only display `WAFD Delivery Trip` records.  Earlier manager
workflows could successfully save an approved `WAFD Loading Record` and then
fail while inserting the delivery trip because of a later validation.  That
left a split operational state: loading existed, trip did not, and the driver
received a misleading empty screen.

## Changes

- Reconciles approved Loaded/Dispatched loading records with their delivery
  trips during migration and whenever the field-delivery page is refreshed.
- Repairs an existing trip's canonical driver and explicit login assignment.
- Creates a missing trip idempotently while preserving normal Frappe document
  validations and row-level driver isolation.
- Uses the same reconciliation path for the manager's Create Delivery Trip
  action, migration, manager field-delivery page, and driver My Trips page.
- Replaces the silent empty state with a multilingual operational explanation:
  no approved loading, incomplete assignment, or blocked trip validation.
- A blocked legacy record no longer prevents other employees' valid trips from
  being reconciled and displayed.

## Deployment requirement

Deploy the release through the normal Frappe Cloud app deployment so site
migration runs.  Verify that the Installed Applications version is
`10.0.0rc247`, then clear site cache and refresh the driver session.

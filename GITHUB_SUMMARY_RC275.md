## Summary

Replace public beneficiary delivery links with managed employee accounts and correct mobile date rendering.

- adds a Delivery Data Viewer task to Employee Management
- supports beneficiary login by name, email and temporary password like other employees
- keeps the account compatible with additional WAFD tasks in the future
- lets Delivery Supervisor assign each trip to one or more named beneficiary accounts
- shows each beneficiary only the deliveries assigned to their own account
- provides a polished read-only screen with driver, mobile, plate, timeline, receiver and delivery photo
- removes public link and expiry-date creation from the supervisor interface
- fixes reversed or merged date display in Arabic delivery dialogs on iPhone and Android

## Upgrade

Run migrate, clear cache and restart after installing RC275.

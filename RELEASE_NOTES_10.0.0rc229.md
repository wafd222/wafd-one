# WAFD ONE 10.0.0 RC229

## Hotel creation UX
- Stops relying on Frappe's generic `Create a new WAFD Hotel` Link flow inside undertakings.
- Adds a clear `+ إضافة فندق جديد / Add New Hotel` button directly below the Hotel field.
- The dedicated dialog contains Arabic Hotel Name, English Hotel Name, District and Save.
- After successful creation inside an undertaking, the new hotel is selected automatically.
- Adds `إضافة فندق` as a dedicated card on the Undertaking Officer home screen for pre-creating a missing hotel.
- Existing RC224/RC227 server-side officer permission checks remain in place.

## Mobile navigation
- Hides the global WAFD back button while any Frappe modal/dialog is open, preventing it from covering Save or dialog content.
- Back navigation remains unchanged outside dialogs.

## Migration
RC229 preserves the corrected RC227 catalogue migration from RC228. If RC227 migration previously failed, deploy RC229 and run migrate again.

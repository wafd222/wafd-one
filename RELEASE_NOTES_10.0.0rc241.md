# WAFD ONE 10.0.0 RC241

## Late trip timing validation fix

- Fixes `Arrival cannot be before departure` when the actual loading time is later than the scheduled arrival target.
- Allows the manager to create the trip from an already documented loading record without re-uploading the photo.
- Preserves the original planned-arrival target so delay calculation and operational auditing remain accurate.
- Keeps the visible RC240 loading-photo button and the secure RC239 driver workflow unchanged.

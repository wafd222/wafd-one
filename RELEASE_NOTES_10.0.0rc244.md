# WAFD ONE 10.0.0 RC244

## Driver identity link fix

- Fixes **My Trips** showing no records when an existing trip still references an older, unlinked WAFD Driver record.
- Recognises a legacy driver record only when both its driver name and normalized mobile number exactly match the record linked to the signed-in driver (including the safe account suffix used for duplicate names).
- Never treats a driver record linked to another user as an alias, even when names or mobile numbers match.
- Applies the same resolved identity to list queries, document permissions and delivery-proof permissions.
- Canonicalizes new delivery trips to the unique enabled driver login record when a legacy unlinked driver is selected.
- Keeps manager field delivery, private camera uploads, multilingual notes and RC243 security restrictions unchanged.

## WAFD ONE 10.0.0 RC244 — Driver Identity Link Fix

RC244 fixes the driver portal showing **no assigned trips** when an existing trip references an older WAFD Driver record while the driver's login is linked to a newer duplicate record.

### What changed

- Resolves the signed-in driver's canonical and legacy records using an exact normalized **driver name + mobile number** identity.
- Keeps records linked to another user completely outside the driver's access.
- Applies the resolved identity consistently to My Trips, document permissions, delivery proofs and private delivery images.
- Canonicalizes future trips to the unique enabled driver login record.
- Preserves manager delivery access, secure camera uploads, multilingual notes and all RC243 restrictions.

### Verification

- RC244 driver identity regression validation passed.
- Python syntax validation passed.
- Release metadata validation passed.
- Patch-path validation passed with 179 entries.

### Deployment

Install/update the app, run `bench --site <site-name> migrate`, clear cache, then fully close and reopen the driver's browser/PWA before opening **My Trips**.

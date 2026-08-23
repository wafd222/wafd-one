# WAFD ONE 10.0.0 RC228
- Fixes the RC227 migrate failure shown on Frappe Cloud.
- Root cause: catalogue `verification_status` contained an OTA-specific phrase that is not one of the WAFD Hotel Select field options.
- Normalizes all verification status, zone and proximity values against the actual DocType options before insert/update.
- Keeps the RC227 employee hotel Quick Entry and bilingual hotel catalogue changes.
- RC227 patch is corrected in place because the failed patch was not recorded as completed; the next migrate safely reruns it.

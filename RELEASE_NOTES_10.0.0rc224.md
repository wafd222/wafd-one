# WAFD ONE 10.0.0 RC224

Focused undertaking usability release based on the validated RC223 baseline.

## Changes
- WhatsApp/iOS PDF share title now uses the selected hotel's English name; the PDF filename remains the undertaking number only.
- Undertaking Officers can add a new hotel from the undertaking flow.
- Inline hotel creation requires an English hotel name so the share caption can remain English.
- Server-side hotel creation is strictly role-gated and does not grant officers write/delete rights over existing hotels.
- RC224 migration patch removes stale Undertaking Officer Custom DocPerm overrides for WAFD Hotel and reloads the source permission matrix.

No undertaking template, signature, stamp, PDF layout, save-to-preview flow, or manager-access behavior was changed.

# WAFD ONE 10.0.0 RC154 — Quality / CCP Stabilization

## Confirmed fixes from live testing
- Fixed CCP validation for minimum-only checks such as Cooking and Hot Holding: an empty Float shown as `0.000` is no longer treated as a real maximum limit.
- Cooking example `Measured 80°C / Minimum 74°C / Maximum 0.000` now validates as compliant without the false “Minimum limit cannot exceed maximum limit” error.
- Cold Holding remains maximum-only; unrelated minimum values are ignored.
- Quality Inspector receives read/select access to WAFD Catering Project so linked Project data can be resolved while working with Production Batches.
- Food-safety preparation/release endpoints no longer require broad write permission on Production Batch; they use read access plus the existing explicit Quality Inspector role guard for verification/release.
- Existing verified CCP records remain protected from editing/deletion.

## Scope
Stability/permission correction only. No redesign and no unrelated workflow additions.

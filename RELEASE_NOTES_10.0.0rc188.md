# WAFD ONE 10.0.0 RC188

## Undertaking mobile actions and signature repair

- Added a visible action bar inside Hotel Undertaking forms for Preview, Approve & Generate PDF, Share PDF, and Save PDF.
- Added visible signature/stamp state indicators inside the undertaking action bar.
- Added an application-wide mobile Back button while preserving native iOS swipe-back behavior.
- Fixed legacy/submitted undertakings where the default company signature existed in Print Settings but was not persisted before PDF rendering.
- Document Studio now fills default undertaking signature/stamp on the render copy so Preview and generated PDF use the same assets.
- Added a migration patch to backfill missing signature/stamp values on existing undertakings and repair only the signature/stamp image bindings of the approved Document Studio undertaking template without changing its layout.
- Kept the existing undertaking design, operational workflow, permissions, finance logic, and project lifecycle unchanged.

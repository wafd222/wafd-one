# WAFD ONE 10.0.0 RC213

## Undertaking private-file permission repair

- Added a server-side, least-privilege File permission bridge for `WAFD Undertaking Officer`.
- Officers may read only files attached to their own `WAFD Hotel Undertaking` records.
- Officers may read only the exact company signature/stamp assets configured for undertaking printing.
- No general File read/write/delete permission is granted.
- Converted the internal `generated_pdf` field from an Attach UI control to a hidden Data reference; PDF access continues through the secured download endpoint.
- Converted the hidden undertaking copies of company logo/signature/stamp from Attach Image controls to internal Data references, eliminating browser-side private-file probes while preserving the approved assets in preview/PDF.
- Preserved undertaking preview, issue, save, share, signature/stamp locking, terms, navigation, multi-user workflow, and the RC212 iOS sound suppression.

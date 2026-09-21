# WAFD ONE 10.0.0 RC328

## Iftar camera-only evidence + supervisor task visibility + handover save fix

- Replace Frappe Attach/Image evidence controls on the Iftar Site Manager and Iftar Supervisor screens with direct camera capture inputs.
- Site inspection, supervisor handover, distribution evidence, and closeout evidence are now captured from the device camera instead of the file/library picker workflow.
- Add a restricted Iftar camera upload endpoint that stores evidence privately and returns the saved File URL.
- Fix Site Manager handover confirmation by updating only Site-Manager-owned handover fields instead of re-saving supervisor-owned report details/photos.
- Clear the assigned supervisor cache immediately after handover so the task becomes visible without waiting for another login cycle.
- Correct the dedicated Site Manager / Supervisor Page module metadata from `Wafd One` to the canonical `WAFD ONE` and reload both page records during migration.
- Preserve RC327 child-table fix, RC320 dedicated Iftar driver screen, and RC317 offline-first driver behavior.

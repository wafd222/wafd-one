# WAFD ONE v2.5.0 — Clean Migration Fix

## Confirmed root cause
Earlier releases executed custom metadata patches that attempted to insert or
reload the WAFD ONE workspace before Frappe had completed normal DocType model
synchronization. Workspace link validation therefore failed for valid DocTypes
such as WAFD Mission, WAFD Hotel and WAFD Contract.

## Fix
- Removed all custom metadata patches from `patches.txt`.
- Kept role creation in `before_migrate`, before permission rows are synced.
- Allowed Frappe v16 to perform its standard DocType model synchronization.
- Reloaded the standard workspace only in `after_migrate`, after all linked
  DocTypes exist.
- Removed forced partial DocType reload logic and overlapping legacy patches.
- Unified application version as 2.5.0 in both package metadata and Python.

## Verification performed
- Parsed every JSON file successfully.
- Compiled every Python file successfully.
- Confirmed all workspace links match DocType JSON names in the repository.
- Confirmed all Table field options match child-table DocTypes.
- Confirmed all Link field options either match WAFD ONE DocTypes or standard
  Frappe/ERPNext DocTypes.

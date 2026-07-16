# WAFD ONE v2.4.3

## Confirmed root cause

The repository contained older patches importing `apply_setup`, while the current
`wafd_one/setup.py` no longer defined that function. Metadata repair was also limited
to part of the application, so a site could finish deployment without loading all
WAFD DocTypes into its database.

## Fix

- Restored a backward-compatible `apply_setup()` entry point.
- Added deterministic synchronization for all 28 WAFD ONE DocTypes.
- Loads child tables first, then masters and transactional DocTypes.
- Rebuilds the Workspace only after all seven linked DocTypes exist.
- Added a new post-model-sync patch for sites where previous patches were already run.
- Runs the same repair in `after_migrate` as an additional safety net.
- Aligned package and runtime version numbers to 2.4.3.

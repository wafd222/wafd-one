# WAFD ONE 10.0.0rc30

## Migration hotfix

- Corrected the RC29 patch declaration in `wafd_one/patches.txt`.
- Frappe patch entries now reference the patch module, while the module exposes its standard `execute()` function.
- Preserved the RC29 production stability, audit-reference, and non-blocking deadline fixes.
- Added validation that every active patch entry resolves to an existing Python module.

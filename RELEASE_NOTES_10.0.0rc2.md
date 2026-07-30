# WAFD ONE Enterprise v10.0.0 RC2

## Migration hotfix

- Converted the v10 launch-center migration from a single Python module into a proper patch package.
- Preserved the existing patch path so failed migrations can safely retry.
- Verified every entry in `wafd_one/patches.txt` resolves to an importable patch module.
- No operational records or existing schema definitions are deleted.

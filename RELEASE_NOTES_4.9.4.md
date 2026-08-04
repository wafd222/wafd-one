# WAFD ONE 4.9.4

## Migration reliability fix

- Corrected the v4.9.3 patch path in `wafd_one/patches.txt`.
- The migration now calls `wafd_one.patches.v4_9_3.execute` exactly once.
- Synchronized package versions in `pyproject.toml` and `wafd_one/__init__.py`.
- Audited all registered patch paths, Python syntax, JSON files, and central-area hotel reference CSV structure.

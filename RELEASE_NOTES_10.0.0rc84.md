# WAFD ONE 10.0.0 RC84

- Corrected the Frappe app Python package layout.
- Moved `hooks.py`, runtime modules, config, public assets, patches, and metadata into the installable `wafd_one` package.
- Fixes Frappe Cloud build failure: `No module named 'wafd_one.hooks'`.
- Retains the RC80 Iftar project module and the child DocType migration fixes.

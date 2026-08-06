# WAFD ONE 10.0.0 RC121

- Fixed Iftar wizard navigation and creation button event handling.
- Reset wizard fields after successful project creation.
- Removed the incorrect 25-meal minimum per table owner; carton capacity remains 25 and partial final cartons are supported.
- Forced Iftar print formats to use no external letterhead, compact A4 margins, and the same Jinja HTML for preview and PDF.
- Added migration patch to update existing Print Format records and clear cache.

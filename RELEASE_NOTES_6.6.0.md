# WAFD ONE 6.6.0 — Document Studio

## New
- Added **WAFD Document Studio**, an in-app visual designer for editable A4 document templates.
- Added draggable/resizable text, dynamic fields, images, logo, stamp, signature, line, table and QR placeholder elements.
- Added RTL/LTR support, page orientation, dimensions and margin controls.
- Added secure preview and PDF generation using Frappe's server-side Jinja and PDF engine.
- Added template versioning, default-template enforcement and role-based permissions.
- Added initial editable templates for hotel undertakings, contracts, quotations, invoices, operation/production/preparation/loading orders, delivery notes and certificates.
- Added a Workspace shortcut to the studio.

## Safety
- Existing business data and existing print formats are not deleted or overwritten.
- Only missing starter templates are inserted during migration.
- Template write access is limited to System Manager and WAFD Operations Manager.

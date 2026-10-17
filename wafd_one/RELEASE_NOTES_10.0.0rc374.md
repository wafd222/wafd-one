# WAFD ONE 10.0.0rc374 — Iftar Report Evidence & Sharing Repair

- Fixes final-report sharing from the report preview: the Share action now obtains the approved PDF and shares the actual PDF file, falling back to downloading it for sharing from Files where file sharing is unsupported.
- Removes standalone owner-delivery photo cards, supervisor photo galleries, and trip-detail blocks from the external viewer. The viewer shows the requested project/owner summary and operational stage timeline; evidence remains inside the official report.
- Renders the authorized report directly from the bundled official template after the existing exact-project, approval, dispatch, and closure checks. Avoids standard `frappe.get_print` permission checks on linked operational DocTypes that the read-only external viewer is not granted.
- Embeds available local/private report images and signatures as data URIs before preview/PDF generation, so historical reports can display evidence without depending on browser/PDF session cookies to retrieve private files.
- Preserves project-scoped access and leaves hotel delivery screens, hotel delivery data, and unrelated application modules unchanged.

Validation: Python compilation, JavaScript syntax checks, and focused Iftar workflow contract tests run locally. Live Frappe Cloud acceptance testing is still required for device-specific PDF sharing and existing private-file availability.

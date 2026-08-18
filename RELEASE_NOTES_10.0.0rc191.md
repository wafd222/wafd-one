# WAFD ONE 10.0.0 RC191

## Undertaking PDF hotfix
- Corrected the PDF image-sanitizer regular expressions introduced in RC190.
- `<img src=...>` and CSS `url(...)` references are now actually detected before wkhtmltopdf runs.
- Local Frappe assets/files are embedded as data URIs; unresolved image references are removed so a missing logo/signature/stamp cannot abort PDF generation with `broken image links`.
- No business workflow, permissions, finance, or undertaking layout changes.

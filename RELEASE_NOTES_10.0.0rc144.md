# WAFD ONE 10.0.0rc144

## Verified fixes retained from RC143
- Report Center project/day selectors use plain text/numeric labels and do not inject HTML markup into Select options.
- Official daily report distinguishes planned assistants from actual attendance, absence and check-out records.
- Operational stage quantities remain sourced from the real daily execution fields.

## RC144 QA hardening
- Added a migration-safe cache refresh patch so Desk Page JS and Print Format metadata are refreshed immediately after deployment.
- Revalidated all Python sources, DocType/Print Format/Page JSON files, JavaScript syntax, internal Python imports, DocType controller presence and patch-module paths.
- Repacked the release without Python bytecode/cache artifacts.

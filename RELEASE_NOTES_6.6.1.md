# WAFD ONE 6.6.1 — Document Studio Reviewed Fix

- Fixed the v6.6.0 migration patch packaging so `wafd_one.patches.v6_6_0.execute` resolves correctly.
- Fixed Document Studio route options so templates open automatically from forms and template records.
- Fixed HTML preview responses to render inline instead of being JSON-wrapped by the API.
- Added strict validation for page size, orientation, direction, and margins.
- Added stored-markup safety checks for element HTML, inline CSS, and custom CSS.
- Replaced fragile dynamic-field/date Jinja expressions with safe `doc.get(...)` expressions.
- Added constrained selectors for page settings in the visual designer.
- Revalidated Python, JSON, JavaScript, patch paths, release metadata, and required DocTypes.

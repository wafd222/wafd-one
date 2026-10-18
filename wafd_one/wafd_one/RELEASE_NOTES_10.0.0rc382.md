# RC382 — External Iftar viewer first-return card fix

- Added a native document capture click handler **only** for the read-only external Iftar viewer card.
- The handler is installed once at script evaluation, independent of the role-home page initialization/render lifecycle; navigation uses the existing `wafd-iftar-authority-viewer` page and `viewer` mode.
- Prevents the ordinary jQuery card handler from duplicating the navigation for this one card.
- Preserved role and authorization checks; no project workflow or other role screen changed.
- Validation: JavaScript syntax check, Python test suite, ZIP integrity. **Safari/iPhone live retest required after deployment.**

# WAFD ONE 10.0.0 RC223

Final consolidated QA release based on the user-validated RC222 baseline.

## Preserved validated behavior
- New undertaking: Save -> direct undertaking preview.
- Managers/reviewers can read all undertakings; officers remain owner-scoped and disabled officers are blocked.
- RC219 route-aware mobile back navigation remains unchanged.
- Undertaking PDF, signature, stamp, issue/save/share workflow remains unchanged.
- Invoice/payment safeguards remain unchanged.

## Final cleanup
- Fixed stale nested package version marker (`wafd_one/wafd_one/__init__.py`) and synchronized all active version metadata to `10.0.0rc223`.
- No schema changes and no new migration patch.
- Release validators, patch paths, Python AST, JSON, JavaScript syntax, asset references and ZIP integrity rechecked.

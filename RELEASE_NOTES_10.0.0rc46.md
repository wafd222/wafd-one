# WAFD ONE 10.0.0 RC46

## Migration hotfix

- Fixed the RC44 Document Studio migration failure caused by the invalid `Undertaking` document category.
- Uses the valid `Hotel Undertaking` category required by the WAFD Document Template DocType.
- Added defensive category normalization and fallback validation in the shared template saver so legacy aliases cannot stop future migrations.
- Kept all RC45 operational workflow and document changes intact.

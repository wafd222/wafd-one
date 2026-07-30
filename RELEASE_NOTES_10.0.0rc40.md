# WAFD ONE 10.0.0rc40

- Fixed Jinja parsing failure in Hotel Undertaking Document Studio PDF caused by escaping dynamic image expressions into `&quot;`.
- Added compile-time Jinja syntax validation for Document Studio templates.
- Recompiled and synchronized all invoice and hotel undertaking templates during migration.
- Reduced the fixed printable canvas height to prevent blank trailing PDF pages.
- Rebuilt the hotel undertaking with logo on the right, company details on the left, wider side margins, larger stamp, no one-party explanatory sentence, and structured operational terms.
- Kept Project and Contract optional so hotel undertakings can be created quickly as standalone documents.

# WAFD ONE 6.3.1

Quality-review release for 6.3.0.

- Fixed the hotel-undertaking print template after detecting an undefined Jinja variable.
- Restored display of both the authorized signature and company stamp.
- Removed a hard-coded branch that permanently hid the company stamp.
- Removed duplicated print CSS and stabilized A4 rendering.
- Added release checks for print-template safety, protected reset endpoints, and the 400-row hotel catalog.
- Updated the release validator to read the package version dynamically.

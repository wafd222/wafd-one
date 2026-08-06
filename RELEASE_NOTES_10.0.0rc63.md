# WAFD ONE 10.0.0 RC63

- Fixed the contract cleanup confirmation field so it always remains editable and never appears broken.
- Added automatic adoption of legacy unlinked Issue/Waste/Transfer stock movements only for clearly marked TEST/UAT/DEMO contracts.
- Re-runs stock rollback preflight until same-test-contract legacy consumers are included or a genuine external dependency remains.
- Keeps deletion disabled for real external dependencies, reserved stock, linked movements from another project, and unsafe adjustments.
- Preserves RC61 specialized warehouse routing and RC62 workflow dependency discovery.

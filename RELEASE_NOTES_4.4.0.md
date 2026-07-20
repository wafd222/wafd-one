# WAFD ONE 4.4.0

## Workflow engine stabilization

- Automatically derives packaging status from processed quantities.
- Repairs legacy packaging records that are 100% complete but still marked Planned.
- Automatically records packaging start/end timestamps and current supervisor.
- Allows loading only after a consistent completed packaging state.
- Automatically marks loading as Loaded when vehicle, driver and quantity are complete.
- Preserves quantity, quality and duplicate-loading validation gates.

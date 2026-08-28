# WAFD ONE 10.0.0 RC242

## Driver-owned actual departure time

- Fixes `Actual departure cannot be in the future` during manager trip creation.
- Manager approval now confirms loading and creates the trip without recording departure.
- Actual departure is recorded only when the assigned driver presses **Start Trip**.
- Clears premature dispatch timestamps left on the current loading record when approval is retried.
- Repairs premature actual timestamps on planned or loaded trips before validation.
- Keeps the loading photo, uploader audit, planned arrival target and all RC239-RC241 security fixes unchanged.

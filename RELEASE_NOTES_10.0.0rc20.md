# WAFD ONE 10.0.0rc20

- Fix Production Batch save deadlock caused by material issue validation.
- Save remains available while the batch is Planned.
- Start Production now uses a server-side action that checks posted material issues before changing status.
- Complete Production now uses a controlled server-side action and quantity dialog.

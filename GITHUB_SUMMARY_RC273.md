## Summary

Add secure read-only delivery tracking for selected beneficiaries.

- adds a per-trip tracking share with viewer name, expiry, access count, and revocation
- adds a responsive public read-only delivery page without requiring a system account
- shows meal loading data, driver name/mobile, plate number, task acceptance, departure, arrival, receiver, and delivery proof photo
- proxies private proof images only after validating the active share token and its linked trip
- adds a Share Tracking action to current and delivered trip cards
- records the driver's task acceptance time when the driver starts the trip
- excludes inventory, pricing, emails, notes, GPS, and unrelated trip data from the shared response

## Upgrade

Run migrate, clear cache, and restart after installing RC273.


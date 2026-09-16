# WAFD ONE 10.0.0 RC308

## Driver Offline-First Home & Automatic Sync

- Keeps the existing RC293 offline delivery queue and IndexedDB data fully compatible; no driver cache reset is required.
- Preloads the driver's assigned trips automatically from the role home whenever a connection is available, so the driver no longer has to open My Trips first just to prepare the offline cache.
- Replays pending offline start/arrival/delivery-proof actions from the role home when connectivity returns, then downloads the latest assigned trips and saves them back to the phone.
- Adds a clear driver connectivity bar on the home screen: online, offline, syncing, or sync-pending state.
- Keeps the driver's local trip cache available while offline and preserves queued photos, signatures, GPS, quantities, notes, and captured action times from RC293.
- Suppresses repeated Frappe "Connection Lost / You are not connected to Internet" notices for driver-only field accounts and replaces them with one controlled WAFD connection status.
- Makes driver language switching local-first while offline; the chosen language remains usable without a server call.
- Rechecks and refreshes the driver's local cache whenever the driver returns to the home screen while online.
- Does not change management, undertaking, quotation, Iftar, finance, inventory, or delivery-supervisor workflows.

### Operating rule

The driver must sign in successfully at least once while connected. After the trip data has been cached on the phone, field actions continue without Internet and synchronize automatically when connectivity returns.

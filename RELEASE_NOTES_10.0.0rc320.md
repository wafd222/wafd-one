# WAFD ONE 10.0.0 RC320

## Dedicated Iftar Driver Screen
- Adds a separate driver screen for Iftar Saim deliveries only.
- Keeps ordinary delivery projects on the existing Driver Trips screen and excludes Iftar trips from it.
- Iftar trips are filtered server-side before sequencing so unrelated projects cannot hide or delay the Iftar task.
- Preserves the RC317 offline-first capture, IndexedDB queue, photos, GPS, notes, receiver data and reconnect synchronization.
- Uses a separate offline cache key for the Iftar driver screen while sharing the safe pending-action queue.
- Adds a dedicated `توصيل إفطار الصائم` card to the Driver home screen and keeps `رحلاتي الأخرى` for normal deliveries.
- No changes to Delivery Supervisor allocation logic, Undertaking, Quotation, Inventory, Cleaning, Finance, or non-driver Iftar stages.

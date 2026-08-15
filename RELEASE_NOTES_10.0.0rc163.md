# WAFD ONE 10.0.0rc163

## Driver row-level security
- Adds **System User** linkage to `WAFD Driver`.
- A user with only the `WAFD Driver` operational role can list/open only delivery trips assigned to the linked driver record.
- Direct URL access to another driver's trip is denied by a document-level permission hook.
- Delivery Proof list/document access follows the same linked-driver boundary.
- Driver users still cannot create Delivery Trips; existing operational status actions remain available on their own trips.
- Operations Manager, Delivery Supervisor, Project Manager and System Manager retain their existing broader role access.
- Migration auto-links legacy data only when there is exactly one unlinked driver and one eligible unlinked WAFD Driver system user; otherwise no guess is made.

No historical project, invoice, stock, trip or delivery data is modified except the safe one-to-one user link described above.

# WAFD ONE 10.0.0 RC156 — Consolidated Permissions Repair

- Consolidates permissions for all WAFD operational roles and clears stale Role Permission Manager overrides.
- Fixes Production Supervisor lookup access to Catering Project and dependent planning data.
- Keeps Quality Inspector focused on quality/CCP work: read-only visibility of packaging/loading, no delivery-stage authority.
- Quality approval now creates the packaging hand-off server-side without granting broad Production Batch or Packaging write access.
- Packaging approval is limited to Production Supervisor / Operations Manager.
- Loading dispatch and Delivery Trip creation are limited to Delivery Supervisor / Operations Manager.
- Driver can update Delivery Trip progress while retaining least privilege.
- Finance can read delivery/receiving evidence needed to validate invoicing.
- Project Manager receives read-only operational and finance visibility where required.
- Reapplies ERPNext lookup permissions for Item, Item Group, UOM and Warehouse.
- Normalizes Desk-enabled WAFD roles and reloads WAFD Page metadata.

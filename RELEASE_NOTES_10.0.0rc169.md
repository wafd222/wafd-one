# WAFD ONE 10.0.0 RC169 — Client Portal

- Adds a secure mobile-first external portal at `/wafd-client` for missions, companies, Haram/mosque staff and other beneficiary entities.
- Adds website-only role `WAFD Client Portal User` (Desk access disabled).
- Adds explicit per-user/per-project mapping via `WAFD Client Portal Access`; no client can see an unassigned project.
- Shows only operational tracking data: planned meals, production, quality, packaging, loading, transit, arrival and receipt.
- Shows vehicle/timing/delivery quantities required for operational follow-up without exposing inventory, suppliers, costs, prices, profit or other clients.
- Adds client receipt acknowledgement as a separate audit record that does not alter internal Receiving Note, invoicing or stock workflows.
- Keeps the internal employee mobile dashboards and executive dashboard unchanged from RC168.

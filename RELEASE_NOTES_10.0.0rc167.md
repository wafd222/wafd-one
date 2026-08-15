# WAFD ONE 10.0.0 RC167 — Cleaning Supervisor UI Hardening

- Keeps the approved RC166 executive dashboard and visual identity unchanged.
- Restricts the Cleaning Supervisor inventory hub to two purpose-built entries only: **Cleaning Supplies Stock** and **My Issued Cleaning Materials / Movements**.
- Hides general stock balances, warehouses/cold rooms, food materials, procurement plans, and purchase orders from the Cleaning Supervisor navigation.
- Keeps Storekeeper / Operations inventory navigation unchanged and still controlled by existing DocType permissions.
- Preserves server-side row-level security for cleaning warehouses, cleaning stock balances, and cleaning stock movements.
- Does not modify projects, invoices, stock quantities, historical movements, Iftar data, or any business records.

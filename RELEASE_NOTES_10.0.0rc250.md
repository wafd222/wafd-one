# WAFD ONE 10.0.0 RC250

## Standalone catering quotation system

- Adds an independent `WAFD Quotation` document; it does not create or alter contracts, projects, trips, or invoices.
- Captures the customer company, contact, supply location, service period, daily meal count, WAFD menu or customer-requested menu, quantities and prices.
- Calculates inclusive service days, total quantities, subtotal, discount, 15% VAT and grand total on the server.
- Adds draft, approval, sent, accepted, rejected and cancelled workflow actions with explicit approver-role checks.
- Adds an A4 RTL quotation print format with the approved WAFD header, company identity, line items, totals and terms.
- Loads the saved company signature and stamp by default. Two independent form controls hide or show either asset without deleting its stored file, so both can also be hidden.
- Adds quotation access to management, operations, project management, approvers, finance and auditors according to least privilege.
- Adds quotation entry points to the role home and Documents hub.

## Upgrade

Deploy the application, run site migration, clear cache, then sign out and sign in once. Confirm the installed version is `10.0.0rc250`.

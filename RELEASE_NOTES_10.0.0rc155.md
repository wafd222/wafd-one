# WAFD ONE 10.0.0rc155

- Fixed Receiving Note → Invoice integration.
- Confirmed `WAFD Receiving Note` quantities are now billable by the invoice engine.
- Preserved compatibility with legacy `WAFD Delivery Proof` records.
- Prevented double billing when both a Receiving Note and Delivery Proof exist for the same trip.
- Existing invoice anti-duplication logic remains active.

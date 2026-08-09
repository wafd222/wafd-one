# WAFD ONE 10.0.0 RC147

- Fixed Service Acceptance Certificate PDF so the footer stays inside the first A4 page; no trailing second page.
- Enforced a single default WAFD Catering Project document template to prevent legacy certificate templates from being selected unpredictably.
- Added transition click-locks for Daily Plan → Production, Production → Packaging, Packaging → Loading, and Loading → Delivery.
- Added server-side duplicate guards for Production Batch per Meal Plan and Packaging Record per Production Batch.
- Preserved RC146 VAT-exclusive profitability logic and the already-validated operational/financial workflow.

# WAFD ONE — Next Release Checkpoint

## Mandatory UI fix

- Localize internal list-page titles into Arabic.
- Prevent mobile title truncation for pages such as Production Batch, Packaging Record, Quality Inspection and CCP Check.
- Make the Iftar Saim operations project table and daily-operation schedule mobile-responsive without clipped columns or awkward horizontal scrolling.
- Do not count an Iftar project whose document/status is Draft as an active project on the operations dashboard; show it as Draft until submitted/activated.
- Block Iftar daily execution approvals (production, packaging, loading, delivery and receipt) while the parent project is still Draft; enable them only after project submission/activation.
- Reduce or reposition the sticky "اعتماد الاستلام" action on the Iftar daily-operation mobile form so it does not cover fields while scrolling.
- Generate the required default assistant-attendance rows for each Iftar daily operation instead of showing an empty table; retain the option to add more rows.
- Do not preselect the Iftar authority food-inspection checklist; require the inspector to confirm each item explicitly, and require the inspection evidence/photo before approval.
- Before allowing Iftar delivery approval, require the operational assignment data (vehicle, driver and supervisor) and prevent completing delivery with blank assignment fields.
- Do not create a separate delivery trip/workflow for Iftar Saim. Link each Iftar daily operation to the existing meal-delivery schedule already assigned by the Delivery Supervisor and shown to drivers; synchronize driver, vehicle, departure, arrival, proof photos, delivered quantity and receipt status back into the Iftar daily operation without duplicating the driver's task.
- Include this fix in the first release after RC297.

## Accepted QA baseline

- RC297 employee role screens and permissions are accepted.
- Fourteen employee tasks, combined-task home merging, and account access were tested successfully.
- Do not reopen the accepted employee-permission scope unless a regression is found.

## Current QA stage

- RC298 implements the role-based Iftar workforce model and is ready for installation QA.
- Test order: management/project setup → kitchen readiness → existing delivery schedule → site receipt/authority inspection → supervisor reports → site-manager approval → official authority report.

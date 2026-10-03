# WAFD ONE 10.0.0 RC352

## Iftar tracking visibility fix

- Hide “متابعة إفطار الصائم” from employees who have not been explicitly assigned Iftar tracking for an active project.
- Keep “بيانات التسليم” available independently for employees assigned the WAFD Delivery Viewer task.
- An employee may receive Delivery Data tracking, Iftar tracking, or both; each is controlled independently.
- Iftar tracking assignment is project-scoped, read-only, and valid during the project period.
- Direct Iftar portal access is also blocked when the Delivery Viewer role exists without a valid project assignment.
- No changes to Undertaking, drivers, Delivery Supervisor, standard Delivery Management, Quotation, Inventory, Cleaning, Finance, or the RC351 operational workflow.

## Verification

- Python syntax check
- JavaScript syntax check
- JSON validation
- All 22 pre-existing regression checks
- New RC352 viewer-visibility regression check

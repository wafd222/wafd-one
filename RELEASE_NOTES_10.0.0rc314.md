# WAFD ONE 10.0.0 RC314

## Iftar Saim practical staged workflow

RC314 adds a new, intentionally simple employee workflow on top of the restored RC144 Iftar program while preserving every unrelated WAFD ONE module.

- Kitchen Supervisor gets one current operating day at a time with three sequential approvals: Production, Packaging, Loading.
- The kitchen screen shows only practical information: contracting entity, site, daily meal count, meal components, additions and carried notes.
- After Loading approval, the assigned Delivery Supervisor receives the day automatically.
- Delivery Supervisor allocates the loaded meals across vehicles/drivers, with meal/carton totals and per-vehicle notes.
- Approved allocations create linked Iftar delivery trips through the existing delivery data model; the delivery module code itself is not modified.
- Workflow notes are carried into delivery trips and remain visible through delivery completion.
- Management and assigned Project Manager get a read-only stage monitor.
- An assigned external viewer (WAFD Delivery Viewer) gets a read-only stage monitor for the contracting/authority representative.
- Management can assign the Project Manager, Kitchen Supervisor, Delivery Supervisor and external viewer from the stage screen.
- Existing restored RC144 Iftar management, daily operation and report center remain available.

## Isolation guarantee

No source files in the Delivery Management, Driver/Offline, Undertaking, Quotation, Inventory, Cleaning or Finance modules are changed by RC314. The only global UI change is adding Iftar-specific entry cards to role home.

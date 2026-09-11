# WAFD ONE 10.0.0 RC276

## Iftar contract and delivery bridge

- Preserves the established **Iftar Saim** projects, daily-operation stages, calculations and reports.
- Adds an optional link from an Iftar project to an existing WAFD contract and catering project.
- Adds a dedicated Delivery Supervisor action for **Iftar delivery**.
- In contract mode, shows the contract, location, date range and meal count, then lets the supervisor select the driver, vehicle and delivery time.
- Keeps standalone Iftar delivery available when there is no contract.
- Labels every Iftar delivery as **contract linked / بعقد** or **standalone / بدون عقد**.
- Shows driver delivery evidence in the Iftar operations page as a separate read-only layer, without changing the established Iftar production-stage totals.
- Adds an Iftar delivery summary to the manager dashboard for the selected date range.
- Safely classifies historical Iftar driver trips as standalone when no contract link exists.

## Upgrade

Install RC276, run migrate, clear cache and restart. Existing Iftar records and previous delivery functions are retained.

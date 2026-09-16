"""RC247: reconcile approved loadings that are missing delivery trips."""

import frappe


def execute():
    from wafd_one.delivery_reconciliation import reconcile_missing_delivery_trips
    from wafd_one.driver_security import repair_trip_assignments

    repair_trip_assignments()
    summary = reconcile_missing_delivery_trips(all_drivers=True)
    if summary["counts"].get("blocked"):
        frappe.log_error(
            title="WAFD RC247 delivery reconciliation",
            message=frappe.as_json(summary, indent=2),
        )
    frappe.clear_cache()

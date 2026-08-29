"""RC245: migrate legacy trips to stable driver-user assignments."""

import frappe


def execute():
    frappe.reload_doc("wafd_one", "doctype", "wafd_delivery_trip", force=True)
    frappe.reload_doc("wafd_one", "doctype", "wafd_invoice", force=True)
    frappe.reload_doc("wafd_one", "doctype", "wafd_payment", force=True)

    from wafd_one.driver_security import repair_trip_assignments

    repair_trip_assignments()
    frappe.clear_cache()

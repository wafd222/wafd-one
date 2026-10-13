"""Install customer delivery schedules and schedule-level follower assignment."""

import frappe


def execute():
    frappe.reload_doc("wafd_one", "doctype", "wafd_delivery_trip", force=True)
    frappe.reload_doc("wafd_one", "doctype", "wafd_delivery_tracking_share", force=True)
    for page in ("wafd_delivery_supervisor", "wafd_delivery_viewer"):
        frappe.reload_doc("wafd_one", "page", page, force=True)
    frappe.clear_cache(doctype="WAFD Delivery Trip")
    frappe.clear_cache(doctype="WAFD Delivery Tracking Share")
    frappe.clear_cache(doctype="Page")
    frappe.clear_cache()

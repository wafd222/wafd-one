"""Install secure read-only delivery tracking links and driver acceptance time."""

import frappe


def execute():
    frappe.reload_doc("wafd_one", "doctype", "wafd_delivery_tracking_share", force=True)
    frappe.reload_doc("wafd_one", "doctype", "wafd_delivery_trip", force=True)
    frappe.reload_doc("wafd_one", "page", "wafd_delivery_supervisor", force=True)
    frappe.clear_cache(doctype="WAFD Delivery Tracking Share")
    frappe.clear_cache(doctype="WAFD Delivery Trip")
    frappe.clear_cache(doctype="Page")
    frappe.clear_cache()


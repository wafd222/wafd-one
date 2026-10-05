"""Complete Delivery Client controller installation after RC285 sync failure."""

import frappe


def execute():
    frappe.reload_doc("wafd_one", "doctype", "wafd_delivery_client", force=True)
    frappe.reload_doc("wafd_one", "doctype", "wafd_delivery_trip", force=True)
    for page in ("wafd_delivery_report", "wafd_delivery_supervisor", "wafd_role_home", "wafd_one_dashboard"):
        frappe.reload_doc("wafd_one", "page", page, force=True)
    frappe.clear_cache(doctype="WAFD Delivery Client")
    frappe.clear_cache(doctype="WAFD Delivery Trip")
    frappe.clear_cache(doctype="Page")
    frappe.clear_cache()

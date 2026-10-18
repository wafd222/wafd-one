"""Refresh supervisor and read-only delivery pages after the RC297 UI update."""

import frappe


def execute():
    frappe.reload_doc("wafd_one", "page", "wafd_delivery_supervisor", force=True)
    frappe.reload_doc("wafd_one", "page", "wafd_delivery_viewer", force=True)
    frappe.clear_cache(doctype="WAFD Delivery Trip")
    frappe.clear_cache(doctype="Page")
    frappe.clear_cache()

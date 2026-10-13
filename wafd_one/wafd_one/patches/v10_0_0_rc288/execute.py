"""Refresh the delivery report page after RC288 UI corrections."""

import frappe


def execute():
    frappe.reload_doc("wafd_one", "page", "wafd_delivery_report", force=True)
    frappe.clear_cache(doctype="Page")
    frappe.clear_cache()

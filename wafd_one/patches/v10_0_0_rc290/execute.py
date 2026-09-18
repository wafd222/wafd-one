"""Reload the delivery report page and clear cached assets for RC290."""

import frappe


def execute():
    frappe.reload_doc("wafd_one", "page", "wafd_delivery_report", force=True)
    frappe.clear_cache(doctype="Page")
    frappe.clear_cache()

"""RC241: refresh delivery timing logic for delayed loading records."""

import frappe


def execute():
    frappe.reload_doc("wafd_one", "doctype", "wafd_delivery_trip", force=True)
    frappe.clear_cache()

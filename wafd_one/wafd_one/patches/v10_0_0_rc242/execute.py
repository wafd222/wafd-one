"""RC242: separate manager loading approval from driver departure."""

import frappe


def execute():
    frappe.reload_doc("wafd_one", "doctype", "wafd_loading_record", force=True)
    frappe.reload_doc("wafd_one", "doctype", "wafd_delivery_trip", force=True)
    frappe.clear_cache()

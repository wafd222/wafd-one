"""Clear driver workflow caches after the shared departure correction."""

import frappe


def execute():
    frappe.reload_doc("wafd_one", "page", "wafd_driver_trips", force=True)
    frappe.clear_cache(doctype="WAFD Delivery Trip")
    frappe.clear_cache(doctype="Page")
    frappe.clear_cache()

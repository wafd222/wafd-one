"""Refresh delivery pages after automatic day rollover corrections."""

import frappe


def execute():
    frappe.reload_doc("wafd_one", "page", "wafd_driver_trips", force=True)
    frappe.reload_doc("wafd_one", "page", "wafd_delivery_supervisor", force=True)
    frappe.clear_cache(doctype="WAFD Delivery Trip")
    frappe.clear_cache(doctype="WAFD Delivery Proof")
    frappe.clear_cache(doctype="Page")
    frappe.clear_cache()

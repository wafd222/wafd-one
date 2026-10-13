"""RC243: install unified manager and driver field-delivery access."""

import frappe


def execute():
    frappe.reload_doc("wafd_one", "doctype", "wafd_delivery_proof", force=True)
    frappe.reload_doc("wafd_one", "page", "wafd_driver_trips", force=True)
    frappe.reload_doc("wafd_one", "page", "wafd_role_home", force=True)
    frappe.clear_cache()

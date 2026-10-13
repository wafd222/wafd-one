"""Install the dedicated Iftar trip source and controller."""

import frappe


def execute():
    frappe.reload_doc("wafd_one", "doctype", "wafd_delivery_trip", force=True)
    frappe.reload_doc("wafd_one", "page", "wafd_iftar_team", force=True)
    frappe.clear_cache()

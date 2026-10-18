"""Refresh the simplified Iftar administration and employee screens."""

import frappe


def execute():
    frappe.reload_doc("wafd_one", "page", "wafd_iftar_team", force=True)
    frappe.reload_doc("wafd_one", "page", "wafd_iftar_wizard", force=True)
    frappe.clear_cache()

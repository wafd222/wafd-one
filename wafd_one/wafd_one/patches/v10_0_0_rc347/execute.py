"""Refresh the two isolated Iftar assignment pages."""

import frappe


def execute():
    for page in ("wafd_employee_team", "wafd_iftar_team"):
        frappe.reload_doc("wafd_one", "page", page, force=True)
    frappe.clear_cache()

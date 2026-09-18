"""Refresh the simplified delivery UI and manager employee controls."""

import frappe


def execute():
    for page in ("wafd_role_home", "wafd_delivery_supervisor", "wafd_employee_team"):
        frappe.reload_doc("wafd_one", "page", page, force=True)
    frappe.clear_cache(doctype="Page")
    frappe.clear_cache(doctype="User")
    frappe.clear_cache()

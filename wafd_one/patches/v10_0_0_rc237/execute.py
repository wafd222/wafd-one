"""RC237: refresh employee pages after mobile and navigation fixes."""

import frappe


def execute():
    frappe.reload_doc("wafd_one", "page", "wafd_employee_team", force=True)
    frappe.reload_doc("wafd_one", "page", "wafd_undertaking_team", force=True)
    frappe.clear_cache()

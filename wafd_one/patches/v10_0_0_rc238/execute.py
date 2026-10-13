"""RC238: refresh employee management after iPhone phone normalization fix."""

import frappe


def execute():
    frappe.reload_doc("wafd_one", "page", "wafd_employee_team", force=True)
    frappe.clear_cache()

"""Refresh only the isolated Iftar and Employee Management screens."""

import frappe


def execute():
    for page in (
        "wafd_employee_team",
        "wafd_iftar_team",
        "wafd_iftar_site",
        "wafd_iftar_supervisor",
    ):
        frappe.reload_doc("wafd_one", "page", page, force=True)
    frappe.clear_cache()

"""Refresh the simplified Iftar screens after installing RC309."""

import frappe


def execute():
    for page in (
        "wafd_iftar_team",
        "wafd_iftar_wizard",
        "wafd_iftar_operations",
        "wafd_one_dashboard",
        "wafd_iftar_report_center",
    ):
        frappe.reload_doc("wafd_one", "page", page, force=True)
    frappe.reload_doc("wafd_one", "doctype", "wafd_iftar_daily_operation", force=True)
    frappe.clear_cache()

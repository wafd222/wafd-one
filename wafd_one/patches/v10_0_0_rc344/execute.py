"""Refresh only the dedicated Iftar pages affected by RC344."""

import frappe


def execute():
    for page in ("wafd_role_home", "wafd_iftar_team"):
        frappe.reload_doc("wafd_one", "page", page, force=True)
    frappe.clear_cache()

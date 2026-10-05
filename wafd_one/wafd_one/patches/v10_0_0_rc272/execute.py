"""Refresh the unified Android and iPhone employee home shell."""

import frappe


def execute():
    frappe.reload_doc("wafd_one", "page", "wafd_role_home", force=True)
    frappe.clear_cache(doctype="Page")
    frappe.clear_cache()

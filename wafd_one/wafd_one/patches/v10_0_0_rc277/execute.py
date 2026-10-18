"""Install the isolated read-only beneficiary mobile shell."""

import frappe


def execute():
    for page in ("wafd_delivery_viewer", "wafd_role_home"):
        frappe.reload_doc("wafd_one", "page", page, force=True)
    frappe.clear_cache(doctype="Page")
    frappe.clear_cache()

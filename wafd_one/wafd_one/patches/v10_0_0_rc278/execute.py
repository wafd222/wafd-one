"""Refresh direct field-role routing and isolated mobile pages."""

import frappe


def execute():
    for page in ("wafd_role_home", "wafd_driver_trips", "wafd_cleaning_home", "wafd_delivery_viewer"):
        frappe.reload_doc("wafd_one", "page", page, force=True)
    frappe.clear_cache(doctype="Page")
    frappe.clear_cache()

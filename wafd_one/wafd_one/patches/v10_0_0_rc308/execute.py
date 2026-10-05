"""Refresh driver field pages after installing the RC308 offline-first shell."""

import frappe


def execute():
    for page in ("wafd_role_home", "wafd_driver_trips"):
        frappe.reload_doc("wafd_one", "page", page, force=True)
    frappe.clear_cache()

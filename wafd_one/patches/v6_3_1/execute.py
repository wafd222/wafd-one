"""Reload the corrected hotel-undertaking print format and protected console."""

import frappe


def execute():
    frappe.reload_doc(
        "wafd_one",
        "print_format",
        "wafd_hotel_undertaking",
        force=True,
    )
    frappe.reload_doc(
        "wafd_one",
        "doctype",
        "wafd_administration_console",
        force=True,
        reset_permissions=True,
    )
    frappe.clear_cache()

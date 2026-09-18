"""Recover RC298 installs by ensuring the missing child DocType controller is loadable."""

import frappe


def execute():
    # RC298 can stop during sync_all before its patch runs when this child
    # controller is absent. Reload the child first, then its parent report.
    frappe.reload_doc(
        "wafd_one",
        "doctype",
        "wafd_iftar_supervisor_daily_owner",
        force=True,
        reset_permissions=True,
    )
    frappe.reload_doc(
        "wafd_one",
        "doctype",
        "wafd_iftar_supervisor_daily_report",
        force=True,
        reset_permissions=True,
    )
    frappe.clear_cache()

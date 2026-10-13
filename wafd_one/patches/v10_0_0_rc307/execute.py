from __future__ import annotations

import frappe


IFTAR_DOCTYPES = (
    "wafd_iftar_project",
    "wafd_iftar_daily_operation",
    "wafd_iftar_supervisor_plan",
    "wafd_iftar_supervisor_daily_report",
)


def execute():
    """Reload Iftar role permissions after the controller permission repair."""
    for doctype in IFTAR_DOCTYPES:
        frappe.reload_doc(
            "wafd_one",
            "doctype",
            doctype,
            force=True,
            reset_permissions=True,
        )
    frappe.clear_cache()

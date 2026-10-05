"""Install the audited, sequential Iftar operations workflow."""

import frappe


def execute():
    for doctype in (
        "wafd_iftar_daily_operation",
        "wafd_iftar_supervisor_daily_report",
        "wafd_delivery_trip",
    ):
        frappe.reload_doc("wafd_one", "doctype", doctype, force=True, reset_permissions=True)
    frappe.reload_doc("wafd_one", "page", "wafd_iftar_team", force=True)
    from wafd_one.wafd_one.iftar_team import backfill_unambiguous_project_team
    backfill_unambiguous_project_team()
    frappe.clear_cache()

"""Repair Iftar role dashboards and backfill safe legacy team assignments."""

import frappe


def execute():
    from wafd_one.wafd_one.iftar_team import backfill_unambiguous_project_team

    frappe.reload_doc(
        "wafd_one", "doctype", "wafd_iftar_project",
        force=True, reset_permissions=True,
    )
    backfill_unambiguous_project_team()
    frappe.clear_cache()

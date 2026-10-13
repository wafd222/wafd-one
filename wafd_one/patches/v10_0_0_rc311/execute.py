"""Restore the approved RC144 Iftar UX/behavior while preserving the modern WAFD ONE platform."""

import frappe


def execute():
    # Iftar-only metadata refresh.  We intentionally do not touch unrelated
    # doctypes, delivery/driver data, quotation, undertaking, inventory or finance.
    for doctype in (
        "wafd_iftar_project",
        "wafd_iftar_daily_operation",
        "wafd_iftar_supervisor_plan",
        "wafd_iftar_assistant_attendance",
        "wafd_iftar_carton",
        "wafd_iftar_component",
        "wafd_iftar_daily_photo",
        "wafd_iftar_distribution_recipient",
        "wafd_iftar_haram_zone",
        "wafd_iftar_operating_cost",
        "wafd_iftar_supervisor_plan_assistant",
        "wafd_iftar_supervisor_plan_owner",
    ):
        frappe.reload_doc("wafd_one", "doctype", doctype, force=True)

    for page in (
        "wafd_iftar_wizard",
        "wafd_iftar_operations",
        "wafd_iftar_report_center",
        "wafd_iftar_team",
        "wafd_one_dashboard",
        "wafd_role_home",
    ):
        frappe.reload_doc("wafd_one", "page", page, force=True)

    for print_format in (
        "wafd_iftar_costing_report",
        "wafd_iftar_daily_handover",
        "wafd_iftar_daily_stage_report",
        "wafd_iftar_distribution_cartons",
        "wafd_iftar_ingredients_report",
        "wafd_iftar_official_daily_report",
        "wafd_iftar_project_summary",
        "wafd_iftar_supervisor_receipt",
        "wafd_iftar_supervisor_team_plan",
    ):
        frappe.reload_doc("wafd_one", "print_format", print_format, force=True)

    frappe.clear_cache()

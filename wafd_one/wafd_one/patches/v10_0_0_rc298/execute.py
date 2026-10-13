"""Install Iftar worker roles, screens, reports and least-privilege access."""

import frappe


def execute():
    from wafd_one.setup import ensure_iftar_file_permissions, ensure_roles

    ensure_roles()
    # Child tables must exist before the parent report is synchronized.
    for doctype in (
        "wafd_iftar_supervisor_daily_owner",
        "wafd_iftar_daily_photo",
        "wafd_iftar_assistant_attendance",
        "wafd_iftar_supervisor_daily_report",
        "wafd_iftar_supervisor_plan",
        "wafd_iftar_project",
        "wafd_iftar_daily_operation",
    ):
        frappe.reload_doc("wafd_one", "doctype", doctype, force=True, reset_permissions=True)
    for page in ("wafd_iftar_team", "wafd_iftar_operations", "wafd_role_home"):
        frappe.reload_doc("wafd_one", "page", page, force=True)
    frappe.reload_doc("wafd_one", "print_format", "wafd_iftar_supervisor_daily_report", force=True)
    ensure_iftar_file_permissions()
    frappe.clear_cache()

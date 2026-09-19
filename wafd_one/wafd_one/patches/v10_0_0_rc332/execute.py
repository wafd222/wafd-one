from __future__ import annotations

import frappe


def execute():
    """Install the complete field-evidence workflow without touching non-Iftar modules."""
    doctypes = (
        "wafd_iftar_supervisor_plan",
        "wafd_iftar_supervisor_plan_owner",
        "wafd_iftar_supervisor_daily_owner",
        "wafd_iftar_assistant_attendance",
        "wafd_iftar_supervisor_daily_report",
        "wafd_iftar_daily_operation",
    )
    for name in doctypes:
        frappe.reload_doc("wafd_one", "doctype", name, force=True)
    for page in ("wafd_iftar_site", "wafd_iftar_supervisor"):
        frappe.reload_doc("wafd_one", "page", page, force=True)
    frappe.reload_doc("wafd_one", "print_format", "wafd_iftar_official_daily_report", force=True)
    # Existing plans remain active after the new future-day activation flag is installed.
    frappe.db.sql("""update `tabWAFD Iftar Supervisor Plan` set active = 1 where ifnull(active, 0) = 0""")
    frappe.clear_cache()

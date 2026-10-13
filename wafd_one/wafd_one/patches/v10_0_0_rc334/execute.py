from __future__ import annotations

import frappe
from frappe.utils import cint


def execute():
    """Expose approved site reports and forward already-approved legacy rows."""
    frappe.reload_doc("wafd_one", "doctype", "wafd_iftar_daily_operation", force=True)
    frappe.reload_doc("wafd_one", "page", "wafd_iftar_team", force=True)

    from wafd_one.wafd_one.iftar_team import finalize_daily_report

    operation_names = frappe.get_all(
        "WAFD Iftar Supervisor Daily Report",
        filters={"manager_approved": 1},
        pluck="daily_operation",
        limit_page_length=5000,
    )
    for operation_name in sorted(set(operation_names)):
        if not operation_name or cint(frappe.db.get_value("WAFD Iftar Daily Operation", operation_name, "site_report_approved")):
            continue
        total = frappe.db.count("WAFD Iftar Supervisor Daily Report", {"daily_operation": operation_name})
        approved = frappe.db.count("WAFD Iftar Supervisor Daily Report", {"daily_operation": operation_name, "manager_approved": 1})
        if total and total == approved:
            finalize_daily_report(operation_name)
    frappe.clear_cache()

"""Keep drafts administrative and publish tasks only after project approval."""

import frappe
from frappe.utils import cint


ACTIVITY_FIELDS = (
    "produced_meals", "packaged_meals", "loaded_meals", "delivered_meals", "received_meals",
    "site_receipt_approved", "authority_inspection_approved", "site_report_approved",
    "administration_report_approved", "daily_report_sent",
)


def _remove_untouched_draft_operations():
    """Remove only auto-generated empty rows; approval recreates them safely."""
    drafts = frappe.get_all("WAFD Iftar Project", filters={"docstatus": 0}, pluck="name", limit_page_length=5000)
    if not drafts:
        return
    rows = frappe.get_all(
        "WAFD Iftar Daily Operation",
        filters={"project": ["in", drafts], "docstatus": 0},
        fields=["name", *ACTIVITY_FIELDS],
        limit_page_length=20000,
    )
    for row in rows:
        if any(cint(row.get(field)) for field in ACTIVITY_FIELDS):
            continue
        if frappe.db.exists("WAFD Delivery Trip", {"iftar_daily_operation": row.name}):
            continue
        if frappe.db.exists("WAFD Iftar Supervisor Daily Report", {"daily_operation": row.name}):
            continue
        frappe.delete_doc("WAFD Iftar Daily Operation", row.name, ignore_permissions=True)


def execute():
    for doctype in ("wafd_iftar_project", "wafd_iftar_daily_operation"):
        frappe.reload_doc("wafd_one", "doctype", doctype, force=True)
    for page in ("wafd_iftar_wizard", "wafd_employee_team", "wafd_iftar_team"):
        frappe.reload_doc("wafd_one", "page", page, force=True)
    _remove_untouched_draft_operations()
    frappe.clear_cache()

from __future__ import annotations

import frappe


REPORT_CHILDREN = (
    "WAFD Iftar Supervisor Daily Owner",
    "WAFD Iftar Assistant Attendance",
    "WAFD Iftar Daily Photo",
)
PLAN_CHILDREN = (
    "WAFD Iftar Supervisor Plan Owner",
    "WAFD Iftar Supervisor Plan Assistant",
)


def _orphan_names(doctype):
    rows = frappe.get_all(doctype, fields=["name", "project"], limit_page_length=0)
    return [row.name for row in rows if not row.project or not frappe.db.exists("WAFD Iftar Project", row.project)]


def _delete_rows(doctype, names, children):
    if not names:
        return 0
    for child in children:
        if frappe.db.table_exists(child):
            frappe.db.delete(child, {"parent": ["in", names], "parenttype": doctype})
    frappe.db.delete(doctype, {"name": ["in", names]})
    return len(names)


def execute():
    """Remove only assignments whose Iftar project has already been deleted."""
    orphan_reports = _orphan_names("WAFD Iftar Supervisor Daily Report")
    orphan_plans = _orphan_names("WAFD Iftar Supervisor Plan")
    _delete_rows("WAFD Iftar Supervisor Daily Report", orphan_reports, REPORT_CHILDREN)
    _delete_rows("WAFD Iftar Supervisor Plan", orphan_plans, PLAN_CHILDREN)
    frappe.clear_cache()

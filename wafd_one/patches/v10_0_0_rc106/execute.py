from __future__ import annotations

import frappe


def execute():
    """Refresh Iftar metadata after the final RC106 operational QA fixes."""
    for doctype in ("WAFD Iftar Project", "WAFD Iftar Daily Execution", "WAFD Nationality"):
        if frappe.db.exists("DocType", doctype):
            frappe.clear_cache(doctype=doctype)
    frappe.clear_cache()

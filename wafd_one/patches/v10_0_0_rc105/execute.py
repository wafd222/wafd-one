from __future__ import annotations
import frappe

def execute():
    for dt in ("WAFD Iftar Project", "WAFD Iftar Daily Execution"):
        if frappe.db.exists("DocType", dt):
            frappe.clear_cache(doctype=dt)
    frappe.clear_cache()

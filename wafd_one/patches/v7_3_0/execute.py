import frappe


def execute():
    # DocTypes are synchronized by migrate. Clear stale planning alerts only; no operational data is deleted.
    if frappe.db.exists("DocType", "WAFD Operations Alert"):
        frappe.db.delete("WAFD Operations Alert", {"reference_doctype": "WAFD Procurement Plan", "status": "مغلق / Closed"})

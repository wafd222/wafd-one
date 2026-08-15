import frappe


def execute():
    frappe.reload_doc("wafd_one", "doctype", "wafd_operations_alert", force=True)

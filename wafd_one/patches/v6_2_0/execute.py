import frappe

def execute():
    frappe.reload_doc("wafd_one", "doctype", "wafd_administration_console", force=True, reset_permissions=True)

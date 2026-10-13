import frappe

def execute():
    frappe.clear_cache(doctype="WAFD Iftar Project")
    frappe.clear_cache(doctype="WAFD Iftar Daily Operation")

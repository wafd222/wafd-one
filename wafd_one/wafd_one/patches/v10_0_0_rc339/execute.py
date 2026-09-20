import frappe


def execute():
	frappe.reload_doc("printing", "doctype", "print_format")
	frappe.clear_cache()

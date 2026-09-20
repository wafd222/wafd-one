import frappe


def execute():
	frappe.reload_doc("wafd_one", "doctype", "wafd_iftar_daily_operation")
	frappe.reload_doc("wafd_one", "page", "wafd_iftar_site")
	frappe.reload_doc("printing", "doctype", "print_format")
	frappe.clear_cache()

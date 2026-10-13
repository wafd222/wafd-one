import frappe


def execute():
    frappe.reload_doc("wafd_one", "doctype", "wafd_hotel_undertaking", force=True)
    frappe.reload_doc("wafd_one", "print_format", "wafd_hotel_undertaking", force=True)
    frappe.reload_doc("wafd_one", "workspace", "wafd_one", force=True)

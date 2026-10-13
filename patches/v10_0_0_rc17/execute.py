import frappe


def execute():
    frappe.reload_doc("wafd_one", "doctype", "wafd_hot_cabinet", force=True)
    frappe.reload_doc("wafd_one", "doctype", "wafd_hot_cabinet_allocation", force=True)
    frappe.reload_doc("wafd_one", "doctype", "wafd_packaging_record", force=True)
    frappe.reload_doc("wafd_one", "doctype", "wafd_hotel", force=True)
    frappe.reload_doc("wafd_one", "doctype", "wafd_hotel_undertaking", force=True)
    from wafd_one.setup import ensure_hotel_undertaking_print_format
    ensure_hotel_undertaking_print_format()

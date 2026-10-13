"""Install delivery equipment, contracting entities and delivery reports."""

import frappe


def execute():
    frappe.reload_doc("wafd_one", "doctype", "wafd_delivery_client", force=True)
    frappe.reload_doc("wafd_one", "doctype", "wafd_delivery_trip", force=True)
    frappe.reload_doc("wafd_one", "page", "wafd_delivery_report", force=True)
    frappe.reload_doc("wafd_one", "page", "wafd_delivery_supervisor", force=True)
    frappe.reload_doc("wafd_one", "page", "wafd_role_home", force=True)
    frappe.reload_doc("wafd_one", "page", "wafd_one_dashboard", force=True)
    frappe.db.sql("""update `tabWAFD Delivery Trip`
        set contracting_entity=schedule_customer
        where ifnull(contracting_entity,'')='' and ifnull(schedule_customer,'')!=''""")
    frappe.clear_cache()

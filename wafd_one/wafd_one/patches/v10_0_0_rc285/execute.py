"""Repair multi-day equipment, reusable clients, report preview and date display."""

import frappe


def execute():
    # Re-run spelling normalization because RC283 may already have run before
    # later customer-reported legacy variants were identified.
    from wafd_one.wafd_one.patches.v10_0_0_rc283.execute import execute as correct_hotel_names
    correct_hotel_names()
    for doctype in ("wafd_delivery_client", "wafd_delivery_trip"):
        frappe.reload_doc("wafd_one", "doctype", doctype, force=True)
    for page in ("wafd_delivery_report", "wafd_delivery_supervisor", "wafd_role_home", "wafd_one_dashboard"):
        frappe.reload_doc("wafd_one", "page", page, force=True)
    frappe.db.sql("""update `tabWAFD Delivery Trip`
        set contracting_entity=schedule_customer
        where ifnull(contracting_entity,'')='' and ifnull(schedule_customer,'')!=''""")
    frappe.clear_cache(doctype="WAFD Delivery Trip")
    frappe.clear_cache(doctype="WAFD Delivery Client")
    frappe.clear_cache(doctype="Page")
    frappe.clear_cache()

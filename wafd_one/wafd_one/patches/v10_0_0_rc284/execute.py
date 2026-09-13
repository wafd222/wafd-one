"""Install reporting fields and pages while preserving every delivery workflow."""

import frappe


def execute():
    frappe.reload_doc("wafd_one", "doctype", "wafd_delivery_trip", force=True)
    for page in ("wafd_role_home", "wafd_delivery_supervisor", "wafd_delivery_report", "wafd_one_dashboard"):
        frappe.reload_doc("wafd_one", "page", page, force=True)

    if frappe.db.exists("DocType", "WAFD Delivery Trip"):
        frappe.db.sql(
            """update `tabWAFD Delivery Trip`
               set contracting_entity=schedule_customer
               where (contracting_entity is null or contracting_entity='')
                 and schedule_customer is not null and schedule_customer!=''"""
        )

    frappe.clear_cache(doctype="WAFD Delivery Trip")
    frappe.clear_cache(doctype="Page")
    frappe.clear_cache()

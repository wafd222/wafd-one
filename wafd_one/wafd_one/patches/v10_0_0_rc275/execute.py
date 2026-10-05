"""Install beneficiary employee access and refresh delivery screens."""

import frappe

from wafd_one.setup import ensure_roles


def execute():
    ensure_roles()
    frappe.reload_doc("wafd_one", "doctype", "wafd_delivery_tracking_share", force=True)
    for page in (
        "wafd_employee_team",
        "wafd_role_home",
        "wafd_delivery_supervisor",
        "wafd_delivery_viewer",
    ):
        frappe.reload_doc("wafd_one", "page", page, force=True)
    frappe.clear_cache(doctype="WAFD Delivery Tracking Share")
    frappe.clear_cache(doctype="Page")
    frappe.clear_cache()

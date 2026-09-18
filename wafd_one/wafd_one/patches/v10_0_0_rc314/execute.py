"""Install the RC314 Iftar-only staged employee workflow metadata."""

import frappe


def execute():
    # Only Iftar project/daily-operation metadata and the dedicated Iftar stage
    # page are reloaded. Delivery/driver/undertaking/inventory/finance DocTypes
    # are intentionally untouched.
    frappe.reload_doc("wafd_one", "doctype", "wafd_iftar_project", force=True)
    frappe.reload_doc("wafd_one", "doctype", "wafd_iftar_daily_operation", force=True)
    frappe.reload_doc("wafd_one", "page", "wafd_iftar_team", force=True)
    frappe.clear_cache()

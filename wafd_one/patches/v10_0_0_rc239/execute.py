"""RC239: install secure mobile loading and assigned-driver delivery workflow."""

import frappe


def execute():
    frappe.reload_doc("wafd_one", "doctype", "wafd_loading_record", force=True)
    frappe.reload_doc("wafd_one", "doctype", "wafd_delivery_proof", force=True)
    frappe.reload_doc("wafd_one", "page", "wafd_driver_trips", force=True)
    frappe.reload_doc("wafd_one", "page", "wafd_role_home", force=True)
    frappe.clear_cache()

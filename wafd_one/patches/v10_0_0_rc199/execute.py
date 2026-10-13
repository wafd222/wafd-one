"""RC199: allow undertaking officers to create new hotels while keeping existing hotels read-only."""
import frappe


def execute():
    if frappe.db.exists("DocType", "WAFD Hotel"):
        frappe.reload_doc("wafd_one", "doctype", "wafd_hotel", force=True, reset_permissions=True)
        frappe.clear_cache(doctype="WAFD Hotel")
    frappe.clear_cache()

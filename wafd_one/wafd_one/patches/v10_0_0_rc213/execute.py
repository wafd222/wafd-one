"""RC213 refresh undertaking metadata after removing the generated PDF Attach control."""
import frappe


def execute():
    frappe.reload_doc("wafd_one", "doctype", "wafd_hotel_undertaking", force=True, reset_permissions=False)
    frappe.clear_cache(doctype="WAFD Hotel Undertaking")

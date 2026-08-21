"""RC198: allow undertaking officers full actions on their own undertakings while keeping template fields locked."""
import frappe


def execute():
    if frappe.db.exists("DocType", "WAFD Hotel Undertaking"):
        frappe.reload_doc("wafd_one", "doctype", "wafd_hotel_undertaking", force=True, reset_permissions=True)
        frappe.clear_cache(doctype="WAFD Hotel Undertaking")
    frappe.clear_cache()

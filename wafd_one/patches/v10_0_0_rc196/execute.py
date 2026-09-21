"""RC196: lock undertaking template-controlled fields for Undertaking Officers."""
import frappe


def execute():
    if frappe.db.exists("DocType", "WAFD Hotel Undertaking"):
        frappe.reload_doc("wafd_one", "doctype", "wafd_hotel_undertaking", force=True)
        frappe.clear_cache(doctype="WAFD Hotel Undertaking")
    frappe.clear_cache()

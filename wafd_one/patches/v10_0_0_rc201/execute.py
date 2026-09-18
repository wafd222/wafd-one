import frappe

def execute():
    # RC201: protected signatory is server-filled, so it must not block officer client saves.
    if frappe.db.exists("DocType", "WAFD Hotel Undertaking"):
        frappe.clear_cache(doctype="WAFD Hotel Undertaking")
    if frappe.db.exists("DocType", "WAFD Hotel"):
        frappe.clear_cache(doctype="WAFD Hotel")
    frappe.clear_cache()

import frappe

def execute():
    # Refresh role/page metadata and clear cached role-home definitions.
    for page in ("wafd-role-home", "wafd-iftar-team"):
        if frappe.db.exists("Page", page):
            frappe.clear_cache()
    frappe.clear_cache()

import frappe


def execute():
    """Install the stock-backed handover picker and remove general supervisor entry."""
    frappe.reload_doc("wafd_one", "doctype", "wafd_cleaning_material_usage", force=True, reset_permissions=True)
    frappe.reload_doc("wafd_one", "page", "wafd_storekeeper_home", force=True)
    frappe.reload_doc("wafd_one", "page", "wafd_cleaning_home", force=True)
    frappe.reload_doc("wafd_one", "page", "wafd_role_home", force=True)
    frappe.clear_cache(doctype="WAFD Cleaning Material Usage")
    frappe.clear_cache(doctype="Page")

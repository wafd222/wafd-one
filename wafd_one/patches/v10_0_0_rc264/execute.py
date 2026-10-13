import frappe


def execute():
    """Install the focused storekeeper page without changing other role homes."""
    frappe.reload_doc("wafd_one", "page", "wafd_storekeeper_home", force=True)
    frappe.reload_doc("wafd_one", "page", "wafd_role_home", force=True)
    frappe.reload_doc("wafd_one", "page", "wafd_iftar_operations", force=True)
    frappe.reload_doc("wafd_one", "doctype", "wafd_stock_movement", force=True, reset_permissions=False)
    frappe.reload_doc("wafd_one", "doctype", "wafd_iftar_project", force=True, reset_permissions=True)
    frappe.clear_cache(doctype="Page")
    frappe.clear_cache(doctype="WAFD Stock Movement")

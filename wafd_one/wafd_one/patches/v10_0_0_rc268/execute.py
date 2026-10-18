import frappe


def execute():
    """Refresh the practical Storekeeper home and role entry points."""
    frappe.reload_doc("wafd_one", "page", "wafd_storekeeper_home", force=True)
    frappe.reload_doc("wafd_one", "page", "wafd_role_home", force=True)
    frappe.clear_cache(doctype="Page")

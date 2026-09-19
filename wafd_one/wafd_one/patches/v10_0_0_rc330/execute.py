import frappe


def execute():
    """Reload the repaired supervisor page and role-home navigation assets."""
    frappe.reload_doc("wafd_one", "page", "wafd_iftar_supervisor", force=True)
    frappe.reload_doc("wafd_one", "page", "wafd_role_home", force=True)
    frappe.clear_cache(doctype="Page")
    frappe.clear_cache()

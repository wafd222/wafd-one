import frappe


def execute():
    """Refresh only the Iftar task page and delivery-supervisor page caches."""
    frappe.reload_doc("wafd_one", "page", "wafd_iftar_team", force=True)
    frappe.reload_doc("wafd_one", "page", "wafd_delivery_supervisor", force=True)
    frappe.clear_cache(doctype="Page")
    frappe.clear_cache()

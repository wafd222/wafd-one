import frappe


def execute():
    """Reload the two dedicated Iftar field pages after correcting their module metadata."""
    frappe.reload_doc("wafd_one", "page", "wafd_iftar_site", force=True)
    frappe.reload_doc("wafd_one", "page", "wafd_iftar_supervisor", force=True)
    frappe.clear_cache(doctype="Page")
    frappe.clear_cache()

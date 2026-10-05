import frappe


def execute():
    """Synchronize the canonical hyphenated Iftar Desk Page routes."""
    frappe.reload_doc("wafd_one", "page", "wafd_iftar_site", force=True)
    frappe.reload_doc("wafd_one", "page", "wafd_iftar_supervisor", force=True)
    frappe.clear_cache(doctype="Page")
    frappe.clear_cache()

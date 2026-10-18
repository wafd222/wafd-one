import frappe


def execute():
    """Refresh the guided cleaning receipt/handover screens."""
    frappe.reload_doc("wafd_one", "page", "wafd_storekeeper_home", force=True)
    frappe.reload_doc("wafd_one", "page", "wafd_cleaning_home", force=True)
    frappe.clear_cache(doctype="Page")

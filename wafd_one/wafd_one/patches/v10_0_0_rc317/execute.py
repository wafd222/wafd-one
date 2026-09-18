import frappe


def execute():
    """Reload only the driver page metadata and clear asset/page caches."""
    frappe.reload_doc("wafd_one", "page", "wafd_driver_trips", force=True)
    frappe.clear_cache(doctype="Page")
    frappe.clear_cache()

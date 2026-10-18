import frappe


def execute():
    """Install the dedicated Iftar driver page and refresh only driver-facing page metadata."""
    frappe.reload_doc("wafd_one", "page", "wafd_iftar_driver", force=True)
    frappe.reload_doc("wafd_one", "page", "wafd_role_home", force=True)
    frappe.clear_cache(doctype="Page")
    frappe.clear_cache()

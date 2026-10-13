import frappe


def execute():
    frappe.reload_doc("wafd_one", "page", "wafd_one_dashboard", force=True)
    from wafd_one.setup import rebuild_workspace_from_source
    rebuild_workspace_from_source()
    frappe.clear_cache()

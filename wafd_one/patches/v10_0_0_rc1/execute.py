import frappe

def execute():
    frappe.reload_doc("wafd_one", "page", "wafd_launch_center", force=True)
    frappe.reload_doc("wafd_one", "workspace", "wafd_one", force=True)
    from wafd_one.setup import sync_all_doctypes, reload_workspace
    sync_all_doctypes()
    reload_workspace(force_rebuild=True)
    frappe.clear_cache()

import frappe


def execute():
    frappe.reload_doc("wafd_one", "page", "wafd_one_dashboard", force=True)
    frappe.reload_doc("wafd_one", "page", "wafd_launch_center", force=True)
    frappe.clear_cache()

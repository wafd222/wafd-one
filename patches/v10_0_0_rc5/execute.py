import frappe


def execute():
    """Refresh the two UAT pages and clear cached assets after RC5 styling fixes."""
    frappe.reload_doc("wafd_one", "page", "wafd_one_dashboard", force=True)
    frappe.reload_doc("wafd_one", "page", "wafd_launch_center", force=True)
    frappe.clear_cache()

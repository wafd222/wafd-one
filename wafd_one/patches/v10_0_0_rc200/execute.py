"""RC200: grant undertaking roles access to the dedicated WAFD role home page."""
import frappe


def execute():
    # Reload the standard Page so its role child table is synchronized on existing sites.
    frappe.reload_doc("wafd_one", "page", "wafd_role_home", force=True)
    frappe.clear_cache()

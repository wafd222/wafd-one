import frappe


def execute():
    """Refresh routing after installing the missing legacy PWA launch page."""
    frappe.clear_cache()

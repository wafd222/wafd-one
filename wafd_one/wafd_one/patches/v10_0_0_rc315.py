import frappe


def execute():
    """Refresh caches for the Iftar assignment-role fix only."""
    frappe.clear_cache()

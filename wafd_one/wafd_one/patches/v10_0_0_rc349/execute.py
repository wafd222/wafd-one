import frappe


def execute():
    """Expire cached page/assets after the isolated Iftar mobile repair."""
    frappe.clear_cache()

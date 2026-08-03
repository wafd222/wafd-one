import frappe

from wafd_one.master_data import load_reference_master_data


def execute():
    """Install expanded nationality menus, ingredients and stock placeholders."""
    load_reference_master_data()
    frappe.clear_cache()

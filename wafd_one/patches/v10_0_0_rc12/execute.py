import frappe

from wafd_one.master_data import install_erpnext_inventory_masters


def execute():
    """Install missing ERPNext inventory masters without inventing quantities."""
    install_erpnext_inventory_masters()
    frappe.clear_cache()

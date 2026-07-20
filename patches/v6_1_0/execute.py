import frappe


def execute():
    """Install expanded reference catalogs without deleting or overwriting records."""
    from wafd_one.master_data import load_reference_master_data
    load_reference_master_data()
    frappe.clear_cache()

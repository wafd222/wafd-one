import frappe


def execute():
    # No schema/data migration is required. The release only corrects child-table
    # synchronization logic for Iftar supervisor setup.
    frappe.clear_cache()

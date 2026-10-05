import frappe

def execute():
    # RC323 only adds dedicated Iftar Site Manager and Supervisor pages and
    # refreshes their route metadata. No standard delivery DocType is changed.
    frappe.clear_cache()

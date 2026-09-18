import frappe

def execute():
    # RC123 changes page JS/CSS only; clear website/desk caches so the new wizard and report center are served immediately.
    frappe.clear_cache()

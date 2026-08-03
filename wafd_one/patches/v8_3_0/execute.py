import frappe


def execute():
    # DocType schema is synchronized by migrate. Keep the upgrade additive and
    # do not create or overwrite operational planning records automatically.
    frappe.clear_cache(doctype="WAFD Daily Meal Plan")
    frappe.clear_cache(doctype="WAFD Daily Meal Plan Item")

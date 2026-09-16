"""RC244: activate alias-aware driver trip permissions."""

import frappe


def execute():
    frappe.clear_cache()

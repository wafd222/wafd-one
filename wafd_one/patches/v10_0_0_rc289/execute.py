"""Clear cached Desk assets after extending the supervisor mobile shell."""

import frappe


def execute():
    frappe.clear_cache(doctype="Page")
    frappe.clear_cache()

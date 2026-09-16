"""Clear permission caches after expanding management assignment support."""

import frappe


def execute():
    frappe.clear_cache()

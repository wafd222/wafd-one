"""RC121 migration compatibility patch.

This patch intentionally avoids writing optional Print Format columns that are
not present in every Frappe v16 schema. Print formats are synced from JSON by
Frappe during migration, so the only required action here is cache cleanup.
"""

import frappe


def execute():
    frappe.clear_cache()

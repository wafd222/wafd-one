from __future__ import annotations

import frappe


def execute():
    # RC101 schema is synchronized by migrate. Do not overwrite any operational prices or records.
    frappe.clear_cache()

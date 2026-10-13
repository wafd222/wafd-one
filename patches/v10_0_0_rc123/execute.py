from __future__ import annotations

import frappe


def execute():
    # RC123 changed Desk Page JS/CSS only. Clear cache so the synced assets are used.
    frappe.clear_cache()
